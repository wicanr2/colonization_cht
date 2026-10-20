// 規格065 R102 READY：追加39個既有來源與三張原始圖集，原版規則與資料保持。
// 規格065 R99 READY：85來源共用追蹤；追加113 Main頭像與專屬色盤，既有84來源保持。
// 只觀測原版寫入及合成四倍畫布，不寫入DOS。
package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/draw"
	"image/png"
	"path/filepath"
)

type hdSmallFrame struct {
	paletteSHA                           string
	paletteIndices                       []byte
	scaled100                            bool
	alsoPlain                            bool
	nominal                              [2]uint16
	bufferSaves, bufferRestores          uint64
	ordinal, w, h, encodedLen, opaque    int
	encodedSHA, writesSHA, artSHA, file  string
	artW, artH                           int
	sample, content                      [4]int
	writers                              uint8
	art                                  *image.RGBA
	accepted, rejected, paints, restores uint64
}

var hdSmallFrames = []hdSmallFrame{
	{ordinal: 54, w: 8, h: 12, encodedLen: 86, opaque: 40, encodedSHA: "9a9f9912a1569b2444c4403bb61eba45573247a9a4494840cfdafeca7466d121", writesSHA: "6d1570f488b88b3e63ceef6eaf5c503be8889db1f26cd6c87bdabb7dab2d757a", artSHA: "0abb719aa0518b9ef295d8b9a7aa865105dfb1b1facd9333a6a8c06e0955868a", file: "icons-054.png", artW: 1024, artH: 1536, sample: [4]int{155, 316, 871, 1306}, content: [4]int{0, 2, 8, 12}, writers: 4},
	{ordinal: 5, w: 13, h: 16, encodedLen: 193, opaque: 125, encodedSHA: "8485f409ac9e42446a89fb0bc862036886b90acab2b802a6b13b1d2f32bc68db", writesSHA: "e7237a28a406dcd2ca8eecd2c4533b3ce77109365e4cbb2c89eb65677feaace9", artSHA: "94ebc3642cd0b069229f2e23fa633085ed53d89cf5c9965eafde74d56af99619", file: "icons-005.png", artW: 1131, artH: 1391, sample: [4]int{272, 304, 894, 1097}, content: [4]int{0, 0, 13, 16}, writers: 5},
	{ordinal: 22, w: 7, h: 12, encodedLen: 95, opaque: 54, encodedSHA: "4e5dfa187a19c1850537ea9c54882b2340e62a1020832d30a35e163446753705", writesSHA: "8060465c43a91649d32466a54beb4638d7e8c575a16e9169e96272e13b0860a5", artSHA: "aa2230fc41fa34ccf782fd8b9c3311390add4c33bf380dd31099a63b3b5c44d8", file: "icons-022.png", artW: 957, artH: 1644, sample: [4]int{281, 412, 689, 1239}, content: [4]int{0, 0, 7, 12}, writers: 5},
	{ordinal: 23, w: 8, h: 12, encodedLen: 98, opaque: 54, encodedSHA: "bf1d638baa43334633f4c6020d0304584bf957531b6502f08639b7c20c26d370", writesSHA: "b184cbbcffef180f2ffb2772294f5d00d8df836136f7bac381139e703777f4eb", artSHA: "305d74bd95d0c8bcfba54832a35398b1dd0f367f85bd1a9702cb3b6e968b1c18", file: "icons-023.png", artW: 1024, artH: 1536, sample: [4]int{334, 425, 690, 1114}, content: [4]int{0, 0, 8, 12}, writers: 5},
	{ordinal: 24, w: 8, h: 12, encodedLen: 103, opaque: 65, encodedSHA: "07411abcaceae3539db17046e13607cf5b50ece5f6c5760e4f1af375e134bda6", writesSHA: "8a54b3ff59527cf976d7dc1bb3f829dad74648327c4ae4b10ea58041903e0ac4", artSHA: "b4dfd073993baf0bfdeb2ebc54a8f729226fecda6f3ccbccc7c9bf2175740051", file: "icons-024.png", artW: 1254, artH: 1254, sample: [4]int{423, 250, 914, 996}, content: [4]int{0, 0, 8, 12}, writers: 5},
	{ordinal: 25, w: 10, h: 12, encodedLen: 102, opaque: 63, encodedSHA: "9d046815241dabe7714a688f263e5b773fee79127b85ca6db4d3b6ce7606cb26", writesSHA: "34bda00a14d2563eb81294931f8fdaa36a368b4907841a04535861dbcc631887", artSHA: "5856ff32bdf7ef16ad2a47f548313ea3e19009f4386ab82b9a51bb4cf81e1d6a", file: "icons-025.png", artW: 1145, artH: 1374, sample: [4]int{301, 456, 878, 972}, content: [4]int{0, 1, 10, 11}, writers: 5},
	{ordinal: 26, w: 9, h: 12, encodedLen: 118, opaque: 81, encodedSHA: "e4d500fe234462ff3072bfa41cb02be376e48a6096bf1f53988ca62652764acc", writesSHA: "873f6fd9e256edb772c058b54f5e11cf0b8236a89de28ea87210c5c2447479ef", artSHA: "27aa649ab52f07522d05608b53b39cfb0b7e5a974e69060f197b6ddcc6ae20b2", file: "icons-026.png", artW: 1086, artH: 1448, sample: [4]int{271, 368, 830, 1066}, content: [4]int{0, 0, 9, 12}, writers: 4},
	{ordinal: 27, w: 10, h: 12, encodedLen: 52, opaque: 44, encodedSHA: "d8ddf9a6bb0f6a136552ce621772a112bfc6a776c809d492b72c02bf7ec3c9dd", writesSHA: "9dbf23ccfe1e4d316edffcb5f6390e533f6cb75766bbd6c3786836cfcd6bbe09", artSHA: "02210ba22e632b688253442b8df6c89bb1d909308ac4174b3679ebdd58798dac", file: "icons-027.png", artW: 1374, artH: 1145, sample: [4]int{378, 457, 996, 681}, content: [4]int{0, 3, 10, 8}, writers: 7},
	{ordinal: 28, w: 10, h: 12, encodedLen: 97, opaque: 75, encodedSHA: "e78a0131f19d3ec3298909ba1600067b7fd44ca23787c4656545d283e4ce1e7f", writesSHA: "a1b31ee85a28f0216abc514d1f3a238d2a77e4412ac72242a09c20442a152536", artSHA: "5ce1c6b9c5e01b95273bbc01bab79ec9f0441b93aabee89ca87385c129b14da1", file: "icons-028.png", artW: 1145, artH: 1374, sample: [4]int{293, 453, 848, 939}, content: [4]int{0, 2, 10, 11}, writers: 7},
	{ordinal: 29, w: 10, h: 12, encodedLen: 63, opaque: 40, encodedSHA: "0a7085d1f07d4511d3ae49b380e738287f7374ba320ffb6a7da165c1f99e59ae", writesSHA: "2a0214f4ab0e38b2eccf0b6324445b2c2240fc2f2254cf7cdf5f6806624ae87a", artSHA: "24b862d6f3f1ca8157b03757803891566331006688ef9f45b75d75941ecd2216", file: "icons-029.png", artW: 1145, artH: 1374, sample: [4]int{331, 551, 845, 860}, content: [4]int{0, 3, 10, 9}, writers: 7},
	{ordinal: 30, w: 13, h: 12, encodedLen: 147, opaque: 104, encodedSHA: "bf986fecd7c189b113fbb012e79ce825a55efa06c931bf10743587e2c7921db6", writesSHA: "2c8c8e3bfee11e6e3cb0479a419f80fc02c04844fc78182b5a97d85209137592", artSHA: "c3b187d8aab2f608da297d4924846e9008dbd5344fa85d28f755ea5b43862ab9", file: "icons-030.png", artW: 1305, artH: 1205, sample: [4]int{331, 294, 1000, 977}, content: [4]int{0, 0, 13, 12}, writers: 6},
	{ordinal: 31, w: 7, h: 12, encodedLen: 94, opaque: 64, encodedSHA: "f1cd09ddfe77071ae2056a71500fec06b6a5a81495836795759250a9d483c827", writesSHA: "72426336c347ebb3c424892e77edd7816ab30c829317fbf3835423daaee4ec44", artSHA: "71d212dfcdcca9dd6685196a1afe237784f7674409e2f24e914af811f131ef9c", file: "icons-031.png", artW: 960, artH: 1639, sample: [4]int{324, 530, 636, 1132}, content: [4]int{0, 1, 7, 12}, writers: 7},
	{ordinal: 32, w: 9, h: 12, encodedLen: 103, opaque: 44, encodedSHA: "e45ae24d8df524f594dac9c068312b3977f75440e031f2fa89f4471662dc554a", writesSHA: "2d6663a210b17b07f431bc8f4cb93af141fce3be5e503d45f2013535d514b734", artSHA: "ff9047b9f5f17e2f777146ca98e19b912e69e5a4258a0ddc9d94919a34d0a3f2", file: "icons-032.png", artW: 1086, artH: 1448, sample: [4]int{475, 366, 612, 1083}, content: [4]int{3, 0, 7, 12}, writers: 5},
	{ordinal: 33, w: 8, h: 12, encodedLen: 97, opaque: 68, encodedSHA: "664a76510ae1b7d580f06764e036b93ea59bd8005af46e2338f05d9681d9582e", writesSHA: "a072b7ee98ff1907c3da4d786109f30c276f4acccb484fd5cc220a0b497d0154", artSHA: "83255fe1b54a440377de39a9986eeb006c20a1ea1bec029285a0765be2a7cb83", file: "icons-033.png", artW: 1024, artH: 1536, sample: [4]int{335, 474, 693, 1103}, content: [4]int{0, 1, 8, 12}, writers: 7},
	{ordinal: 34, w: 8, h: 12, encodedLen: 108, opaque: 80, encodedSHA: "85f9d697d6c3524c320269cd2938c157f29c16fce3d8690dc9a82c492f8de9b4", writesSHA: "11c87dfa844fbc3368621b7529133a9e911f754e9b2e8b5eebb79e50ffbae7a7", artSHA: "31b17472008c841982e39c58661f12c6360fd43c69bb2162d9140dcaba69ab7e", file: "icons-034.png", artW: 1024, artH: 1536, sample: [4]int{320, 400, 704, 1136}, content: [4]int{0, 0, 8, 12}, writers: 7},
	{ordinal: 35, w: 9, h: 12, encodedLen: 82, opaque: 55, encodedSHA: "3c3e241e84a8c393bb116d32727cde14476523ff317b459a439e88c7dcb69f2b", writesSHA: "3e263823179b1dabd2ae432f68468c46541e9cd56fbc654d82b290a06f173600", artSHA: "016841a1ce6ee72170fb4a846e462eac95457c5491a2e6f00182aa67fb3d044b", file: "icons-035.png", artW: 1086, artH: 1448, sample: [4]int{315, 543, 821, 977}, content: [4]int{0, 2, 9, 10}, writers: 7},
	{ordinal: 36, w: 9, h: 12, encodedLen: 76, opaque: 38, encodedSHA: "dcd32b8ea53065c46730526a3af71efe9d8ae70d9c8ce7b2f273dd820b3b7b83", writesSHA: "a931d7b927d2e0ea87a35d942dc98a816a07fb36a58832372953f03da4cd960e", artSHA: "43d1a5a0078f788d25583937514eba6d8eac8f96b398f4f950156d4c6e7bc5af", file: "icons-036.png", artW: 1086, artH: 1448, sample: [4]int{296, 477, 808, 977}, content: [4]int{0, 2, 9, 11}, writers: 5},
	{ordinal: 37, w: 6, h: 12, encodedLen: 84, opaque: 48, encodedSHA: "91cc5f35956d73f46088ec2846b061de0964c5d5e2a34ed31def569495bfc019", writesSHA: "3913978deb02749df32517806ae9de3efde18579bf28ac70e09a6c9d24b3dbfc", artSHA: "5ec0f2a0c3cdd4369d76899a93ffe675346ebf8b65cdf2ac4080956dbaffbd44", file: "icons-037.png", artW: 887, artH: 1774, sample: [4]int{361, 469, 584, 1261}, content: [4]int{1, 0, 6, 12}, writers: 6},
	{ordinal: 38, w: 7, h: 12, encodedLen: 95, opaque: 54, encodedSHA: "9f8354e113810f6ca1a3654007189c0816b4183acea23a335bc5d3ea1718ba0b", writesSHA: "ec07b8f7c9bf3b3ccf0ba9c3fb78b4a7bacef44ddfe402a5c1deeada1340d6f1", artSHA: "25eb4306ca4b8510b3cf6487106d138885048df5bfb6588bb39d08e7d16b29f5", file: "icons-038.png", artW: 957, artH: 1643, sample: [4]int{338, 504, 611, 1202}, content: [4]int{0, 0, 7, 12}, writers: 5},
	{ordinal: 42, w: 9, h: 12, encodedLen: 118, opaque: 82, encodedSHA: "c6616b3ba2d5a7f88d8be4a8d482f609d53a0e206bda2668620984206eaaa115", writesSHA: "e0dc59410cc3ffb45ef92e93ffbc31fc827419a0c0aed67c450f97072fe105c2", artSHA: "7f6f1eec0482e8751abf75e120d26d559e1edac12a1c3415061bdcc302be4d04", file: "icons-042.png", artW: 1086, artH: 1448, sample: [4]int{331, 439, 755, 1065}, content: [4]int{0, 0, 9, 12}, writers: 4},
	{ordinal: 53, w: 6, h: 12, encodedLen: 84, opaque: 48, encodedSHA: "7a8771e90e7eb1505174af59bb9c6a8450e880a87bafe3ccaed2ddcea0f9c807", writesSHA: "22352d5acb59d6ffbd90fd92466b4ae54c005cd904709cb65cb6a51d583682ab", artSHA: "e1fa16b2b82b837c47fb363df377e3710957ea46a92cd2bf4adfba0c676ea3b8", file: "icons-053.png", artW: 887, artH: 1774, sample: [4]int{346, 472, 596, 1372}, content: [4]int{1, 0, 6, 12}, writers: 6},
	{ordinal: 56, w: 8, h: 12, encodedLen: 92, opaque: 52, encodedSHA: "d544d624df1f80a1f7c901d4a55d7482d1cfc81a14011c1052204f477b22cd54", writesSHA: "adb2167aed9f21df8bf7a2b6f9f7827d44ab3f70629ab0b07f91125a20a23299", artSHA: "6daf183dc19f65c5a692bd00eea66bbb8706d20dab05ff445b57615a40a06564", file: "icons-056.png", artW: 1024, artH: 1536, sample: [4]int{341, 492, 683, 1038}, content: [4]int{0, 1, 8, 12}, writers: 5},
	{ordinal: 59, w: 6, h: 16, encodedLen: 102, opaque: 58, encodedSHA: "6494ccb207a1532a79de201f7a160381679d39626dd8aa09c0b4c857c2502d7a", writesSHA: "c582b30440a7624b8dc3b7a905dfcf63b3fefe5ec3133a28050aae6ff161317b", artSHA: "2057be1b92f182c4a4b029c77d2d4184117a8d67e7a3d3cec72e80f5ab911dba", file: "icons-059.png", artW: 768, artH: 2048, sample: [4]int{142, 407, 625, 1649}, content: [4]int{0, 2, 6, 16}, writers: 4},
	{ordinal: 62, w: 10, h: 12, encodedLen: 87, opaque: 58, encodedSHA: "af3a93128930bac4335ab2ea5797af85b6586aa78183c4ebcf391a7e84488689", writesSHA: "7c514405c07e722ca9c012144fa0cad78e10e0a7c0160f151afad428d47b4053", artSHA: "e77fc69ec546250f2131cac885f7e7d5eaaa6789650e3455eeb298385c335680", file: "icons-062.png", artW: 1145, artH: 1374, sample: [4]int{384, 441, 762, 901}, content: [4]int{1, 2, 9, 11}, writers: 7},
	{ordinal: 67, w: 14, h: 13, encodedLen: 174, opaque: 182, encodedSHA: "c0a59d055bded77608e9dce440dd20f0307a30db4e347573b567d21bd0692dec", writesSHA: "3932f2356bd8d857d089240e09d6cd865c0190c37c5aca48618e50eba1e2e129", artSHA: "895de84eead2ce925dc3d4aa0c0caa75c2654558a3c3d08c858b0dc90e5fd50b", file: "icons-067.png", artW: 1301, artH: 1209, sample: [4]int{247, 225, 1054, 984}, content: [4]int{0, 0, 14, 13}, writers: 7},
	{ordinal: 68, w: 14, h: 13, encodedLen: 142, opaque: 182, encodedSHA: "f3cbbb381cfd781c4c72f7493f10bba233dfe9dd9de885941486dd584bb35c5b", writesSHA: "76a47c5fd44ccb445f3a6e8a558c28e5c79bb08d289b4eaee3ffc36531a405bc", artSHA: "9cc4ee823734a13f16defc12252e60d1cb679c2200c392b823269eba4a98dd8b", file: "icons-068.png", artW: 1301, artH: 1209, sample: [4]int{224, 241, 1078, 1007}, content: [4]int{0, 0, 14, 13}, writers: 7},
	{ordinal: 69, w: 14, h: 13, encodedLen: 154, opaque: 182, encodedSHA: "aace82dada1a34f849ee054fb58bb7cbf15a892842ead0e56ab2f36bdce411f3", writesSHA: "1207ce8ee462cf5b49257afabdcc8410dfd9c20f64336f2122c1017eeb7f183f", artSHA: "0b379205f3b0c83e2af2dd93ad9d8b2eaf6f24a7c2a86a33063899ce5e202e56", file: "icons-069.png", artW: 1300, artH: 1209, sample: [4]int{252, 235, 1049, 978}, content: [4]int{0, 0, 14, 13}, writers: 7},
	{ordinal: 94, w: 8, h: 16, encodedLen: 122, opaque: 74, encodedSHA: "4bb03debbfdb740e290772799a9c4521cf94edae6c4c90975a738c61be076a6b", writesSHA: "adc7b5afcaf85a2d820b270c1f805c7e5ad7417cc200b249eab0c862e6f3dca2", artSHA: "e82953c98cc131d7298651a5b3d1bb227a542e324dc7833d54b4cb6927d4413d", file: "icons-094.png", artW: 887, artH: 1774, sample: [4]int{187, 397, 700, 1354}, content: [4]int{0, 2, 8, 16}, writers: 6},
	{ordinal: 100, w: 6, h: 16, encodedLen: 101, opaque: 60, encodedSHA: "36d3a8e51b4bce57a879d96703d5fad70797f9e940e13aa3abc4d6f830e4d832", writesSHA: "8cbf8e6a6166f5adfc6fab31349dc9fd7cb6e9b768acd6a89477a9763bd90c0a", artSHA: "", file: "", artW: 0, artH: 0, sample: [4]int{0, 0, 0, 0}, content: [4]int{0, 0, 0, 0}, writers: 6},
	{ordinal: 122, w: 10, h: 12, encodedLen: 119, opaque: 120, encodedSHA: "aa5759026b1970969fa549768d2cbb3780e53a755322286c8175cb4e967c469c", writesSHA: "a7ea9be3ee0969ec902b00eccc7da7f7435e7e6e67637cef95438433bab28e76", artSHA: "6f85e33891c499da120ae419f0d206c618f6bd9af5d6bfd37a9ad95fb51c7da7", file: "icons-122.png", artW: 1145, artH: 1374, sample: [4]int{309, 344, 837, 1001}, content: [4]int{0, 0, 10, 12}, writers: 7},
	{ordinal: 123, w: 13, h: 11, encodedLen: 115, opaque: 98, encodedSHA: "48fcc09dab18d4a0e86729c15b9ef45922a2cf7e4aa1fde41c4857fef8753b29", writesSHA: "77cd510b6a9d0fd344c7097f4ca8fe6f4cd6d66839a76e78f425fbdb5b4ed21f", artSHA: "4458545d6806f17d12b68ba634f5bf617bed20bb78f11fae7da0796cc8296fc1", file: "icons-123.png", artW: 1366, artH: 1151, sample: [4]int{396, 349, 944, 829}, content: [4]int{0, 0, 11, 11}, writers: 7},
	{ordinal: 124, w: 13, h: 11, encodedLen: 117, opaque: 84, encodedSHA: "d69c554722b4abce4daf9b7003381e4103664c21cebf0d7ce48fe0ad1d825d5a", writesSHA: "664e6fddcb19c58f7f44154d821f3754814d556ffdd1e7ba800e204e45e314d2", artSHA: "4e69339b0740bc0c732363eea1eb4bbbe8009aa9a15fda2f1e81bfbb70dca62f", file: "icons-124.png", artW: 1362, artH: 1155, sample: [4]int{401, 352, 961, 790}, content: [4]int{0, 0, 13, 10}, writers: 5},
	{ordinal: 6, w: 13, h: 16, encodedLen: 193, opaque: 121, encodedSHA: "d41bb3d2ec6f99801c5bea52e89bd7f685d291fb74771e0b8a0ff6f3fa7a475a", writesSHA: "44efa85835a73b90633a014cd3049188acf3baeac9fedda5d537ce00c4be1ca7", artSHA: "c862cdfa55ab3de416018c3450dc90c392ed7fd54c7fb5f2a9c31538f23442bb", file: "icons-006.png", artW: 1122, artH: 1402, sample: [4]int{198, 144, 947, 1191}, content: [4]int{0, 0, 13, 16}, writers: 7},
	{ordinal: 7, w: 14, h: 16, encodedLen: 202, opaque: 147, encodedSHA: "b79c1f2ec195747440948fd98198ecae7c3f2d90a59aacdb49a7ce5487afbfce", writesSHA: "c8c67dd14525378d852e8d2c6ad548311c9263cfcad932c99c36b2a5afafbaad", artSHA: "191f23d8ec4b49fbeff41864c0fd812f08b88fd0abbb83255955e3625da647a8", file: "icons-007.png", artW: 1121, artH: 1403, sample: [4]int{167, 176, 980, 1226}, content: [4]int{0, 0, 14, 16}, writers: 6},
	{ordinal: 14, w: 13, h: 16, encodedLen: 191, opaque: 128, encodedSHA: "885ffdbf33dca42e83fd1a93f95ef871fd5efe973f489debd71473200240ddf0", writesSHA: "0e908bb1d2288b022846c4f5c30fbc42ceaf868873ab582161de9d066a77cbc3", artSHA: "22e18c47baaf6f5188d9dcfadd4e69ab41812acaf39274b3f377ae7bba059c39", file: "icons-014.png", artW: 1120, artH: 1404, sample: [4]int{205, 171, 953, 1261}, content: [4]int{0, 0, 13, 16}, writers: 7},
	{ordinal: 15, w: 13, h: 16, encodedLen: 190, opaque: 131, encodedSHA: "84f986d89acd03ed96fc3d6c2e2a68607015491314e320149e81c0c752203e5e", writesSHA: "e7e0bc3d95387a8b2ac05cb1eb0123ad52ea090ed25a8ee9537752abba5b7471", artSHA: "4b938de1299c6c0f5895993715325ad66b8328b9616f5c98fc0f2bce8f09c3a9", file: "icons-015.png", artW: 1122, artH: 1402, sample: [4]int{204, 275, 940, 1116}, content: [4]int{0, 0, 13, 16}, writers: 6},
	{ordinal: 127, w: 14, h: 16, encodedLen: 204, opaque: 155, encodedSHA: "4798a978c18d26b279eb14d9b88ab1880c0c3a9588ccf050d8da432976f43f68", writesSHA: "1f815560ce528714e9f1ccedfa527f5d645dd1059a613c89686bec6dbbb208a5", artSHA: "c18b01f9ab0af49f84184c9fb11bcd582af71b5b8bccd7f3e07b01b2d7e5b235", file: "icons-127.png", artW: 1122, artH: 1402, sample: [4]int{114, 183, 1039, 1256}, content: [4]int{0, 0, 14, 16}, writers: 6},
	{ordinal: 8, w: 14, h: 16, encodedLen: 165, opaque: 141, encodedSHA: "b294109df44f954c1689f958464e24c185d89dee448d04626638d251497bc3c4", writesSHA: "a31787707145198efe15676fcbfd9be368ec38a2bed47668a556e047b993b6d8", artSHA: "19045ad0de2cd24bf172f0dcbb5466ee677e1d3270b741dee66df81e7b2b5203", file: "icons-008.png", artW: 1254, artH: 1254, sample: [4]int{162, 333, 1130, 1181}, content: [4]int{0, 4, 14, 16}, writers: 7},
	{ordinal: 9, w: 14, h: 16, encodedLen: 91, opaque: 67, encodedSHA: "6c0e697e6d80561b66fd03332411f8597a43472d6a49707c0bfe6fe34b975c5e", writesSHA: "b0bf3ecfacab9b795d5149e2e69df005da42cf35c399b6be3ee027735c3a180d", artSHA: "9ae2a857a9f143a9747753d36e5d16dd506b0d2984fac310b20056c926d47ec2", file: "icons-009.png", artW: 1254, artH: 1254, sample: [4]int{102, 443, 1173, 916}, content: [4]int{0, 9, 14, 16}, writers: 7},
	{ordinal: 16, w: 14, h: 16, encodedLen: 118, opaque: 82, encodedSHA: "d665336038923ec16ba48f901f9c96c68dfbf2f6302924854d9269b350208401", writesSHA: "db655afb504c1c1acb9b0664c9fa45376cfc95e0a1fccfdf422c419e15a295b7", artSHA: "edfb3e4e2eed371c6d8fe5fb9c905af05dd62b515fd4b81455e0f50d037e8889", file: "icons-016.png", artW: 1254, artH: 1254, sample: [4]int{122, 342, 1132, 1020}, content: [4]int{0, 7, 14, 16}, writers: 5},
	{ordinal: 58, w: 6, h: 16, encodedLen: 103, opaque: 60, encodedSHA: "d47a00529b4933300873a36285f01c1be346839535aa7ec2877409326377dd88", writesSHA: "a53cee94d328c3c0947270f9973bb0382c74779bc34a09076701eb52fd02d4b5", artSHA: "61743ce80d8c32b180b1cc8c778af73cde0935115f1a83cd0099f2e8cd6179ce", file: "icons-058.png", artW: 887, artH: 1774, sample: [4]int{186, 165, 702, 1568}, content: [4]int{0, 2, 6, 16}, writers: 4},
	{ordinal: 60, w: 6, h: 16, encodedLen: 103, opaque: 60, encodedSHA: "4fff2f332f95ffaad642fc498486dd21d5eaa9ebd9994c9a48f290c26c342a26", writesSHA: "d56ff32fd3b948d4026b41dbe2ce44ce91e72b02aa60bfd31d6eb07f52c55dac", artSHA: "5422ec86e9c250d02fcdfaa731a3d8fdc34fcd3a74ceec5586aae72bd6836224", file: "icons-060.png", artW: 887, artH: 1774, sample: [4]int{179, 261, 712, 1564}, content: [4]int{0, 2, 6, 16}, writers: 4},
	{ordinal: 66, w: 8, h: 16, encodedLen: 120, opaque: 57, encodedSHA: "02593fc59c99b23f76ab63edbea38f5c886a23e71cd58b23247d4f2ce8936682", writesSHA: "17906ee13d8a5cf2391842230d21b78bde5bbaa9b7d8aa1c0f44fddc0965ec90", artSHA: "2ee09b5d97a813fe09b714f45c6ef302b5a9021ba5b260ce7b7c66976cd930de", file: "icons-066.png", artW: 887, artH: 1774, sample: [4]int{199, 278, 766, 1522}, content: [4]int{1, 1, 7, 16}, writers: 4},
	{ordinal: 81, w: 8, h: 16, encodedLen: 121, opaque: 70, encodedSHA: "5a58e4b283a222f351c79bb6202fe24e70b2ae4943556f69453ddcba151b0b89", writesSHA: "9128e4991947c379fe5052efc79214d72b5f558a03e4fd10e0b5bc26b04ccc83", artSHA: "860dbb88125bf15711a9cec5f79429de211203f5a25119834200f01557b570f0", file: "icons-081.png", artW: 887, artH: 1774, sample: [4]int{119, 275, 809, 1589}, content: [4]int{0, 2, 8, 16}, writers: 6},
	{ordinal: 82, w: 6, h: 16, encodedLen: 103, opaque: 60, encodedSHA: "ca5691cab36caacb04d79beca64009b5afa8f12faa9d99c47e43c823994d3b70", writesSHA: "1bca152589a83cc3cabb14ab95e972b0be77e25cc5f388f172e2f0ad4d78a75d", artSHA: "6064d0f3c204d227e3cc202a131b65777a19920f6db007f22889359d412f39c2", file: "icons-082.png", artW: 887, artH: 1774, sample: [4]int{153, 152, 740, 1626}, content: [4]int{0, 2, 6, 16}, writers: 4},
	{ordinal: 83, w: 6, h: 16, encodedLen: 103, opaque: 60, encodedSHA: "8f2678af9fccd87b9c16ba8e19bb2b83d2f8e841cd643351ef6c452fda549815", writesSHA: "2b4152a94e27697b10e2bea8862be35fbf3d975209b83e5926c84948a012b7ee", artSHA: "daebfb120f397c41f2fc68e1e1ea8edf570a27a1f1dff300553234de119100da", file: "icons-083.png", artW: 887, artH: 1774, sample: [4]int{168, 231, 738, 1591}, content: [4]int{0, 2, 6, 16}, writers: 4},
	{ordinal: 84, w: 6, h: 16, encodedLen: 103, opaque: 60, encodedSHA: "0a4156824cd23640c0507bb0b282d2f9006fdf35ea095a7dd6a8434eba9aa7b3", writesSHA: "230e10313fb8295e22a1dee3ddcf7fe5f55dd8df912ac0ff6f0ee1cf1bc0d794", artSHA: "0bc1b2bf46b52a2d038cc4abddcb8617da9b111d6cebabbaeb6dd41336dae201", file: "icons-084.png", artW: 887, artH: 1774, sample: [4]int{178, 267, 730, 1562}, content: [4]int{0, 2, 6, 16}, writers: 4},
	{ordinal: 85, w: 8, h: 16, encodedLen: 123, opaque: 77, encodedSHA: "224d9f8a2bed6e06f60f26bc07304a97de7c5c58bc19264680f95e1684f5a7d3", writesSHA: "3cb0611901681638638528edf8b1e62f5a7970c147d614b7949c82729b9d8e90", artSHA: "f19cd765d4b288c2b56af2d20abaa1bdd0fe0c026da11f98088fe85078c5e203", file: "icons-085.png", artW: 887, artH: 1774, sample: [4]int{97, 173, 790, 1601}, content: [4]int{0, 2, 8, 16}, writers: 4},
	{ordinal: 86, w: 8, h: 16, encodedLen: 116, opaque: 74, encodedSHA: "2c128b56ae588e5dd8464a70de5eccac1a6d8b512b58e08dcc0fa1cad4063326", writesSHA: "3a4e654f7708739ec6b572c4fc4a5b911345a4b8cbb8e5e4fe8b45ca56c59f91", artSHA: "0eb43567c95ccf81cfcc107db10cacaa67d341b358da2043456a7793da8ef8c2", file: "icons-086.png", artW: 887, artH: 1774, sample: [4]int{108, 177, 784, 1635}, content: [4]int{0, 1, 8, 16}, writers: 5},
	{ordinal: 87, w: 8, h: 16, encodedLen: 112, opaque: 68, encodedSHA: "1afa034fc731b6ae04446b65cb9a167ebfc54d602b6e3f6ee6e84d8d4db7d7a8", writesSHA: "a7db80ea9fae9d6ebe9f93157448d027ee5cf0a869ccb8e8471ffdea2e706fea", artSHA: "9e440f2b86014f715a2ba92a9ab583ff71299d0d00f8e66eb77728c98cf460cd", file: "icons-087.png", artW: 887, artH: 1774, sample: [4]int{122, 222, 811, 1561}, content: [4]int{0, 2, 8, 16}, writers: 4},
	{ordinal: 88, w: 8, h: 16, encodedLen: 108, opaque: 65, encodedSHA: "077f475854762306005b69f3d49bdaa891d04b583caa6a6353bd9b2dc23b9649", writesSHA: "41c58ce8d69b9e48c661ef4b6ad4e99675b5fa6ba6a0160c551a7ff6523cf656", artSHA: "418541b1e716f9ff84bdc962eaa1f3c927ff5e7f18aab689b07e96eba55431f7", file: "icons-088.png", artW: 887, artH: 1774, sample: [4]int{111, 194, 812, 1546}, content: [4]int{0, 2, 8, 16}, writers: 5},
	{ordinal: 89, w: 8, h: 16, encodedLen: 128, opaque: 66, encodedSHA: "7a8054fd1f9191ae6cc4b5b9a8ae70ec43796a6648e2bf96443378cd296c4a55", writesSHA: "9703923f7d1bd611b64b020100c7c6ee81508e8059a35a6bb20b725e1d615e91", artSHA: "e8c3874a0308134a36a634cd33201d2fc5350fa5fb8d42517e743e8f371733ad", file: "icons-089.png", artW: 887, artH: 1774, sample: [4]int{113, 242, 794, 1546}, content: [4]int{0, 2, 8, 16}, writers: 4},
	{ordinal: 90, w: 6, h: 16, encodedLen: 96, opaque: 54, encodedSHA: "97a524825a290cc0f16e2f8e8901a7a27e4f0666beb1db90abfba85dfa670102", writesSHA: "136472614e1cd54119ac257b93be31daf249ba653332b27fbcbe44d3cd0b3d0b", artSHA: "304baa75c942ea22384ccddf23edb50556ce87bc5f0fafa9092a6386478d42b7", file: "icons-090.png", artW: 887, artH: 1774, sample: [4]int{155, 242, 749, 1554}, content: [4]int{0, 3, 6, 16}, writers: 4},
	{ordinal: 91, w: 6, h: 16, encodedLen: 96, opaque: 54, encodedSHA: "b7747aa5cbcab61c1c43b27c8f86edd440570b0fa7c9e05650e8fd5cfb92224f", writesSHA: "f89c24949851a745f5a0214344baf143e15a280d01d3c8f1f624c64de499bbb0", artSHA: "6733d1909558a3d29136749d19c79b47489a9ee01869a55220cbcfdb603ddc53", file: "icons-091.png", artW: 991, artH: 1588, sample: [4]int{234, 233, 758, 1412}, content: [4]int{0, 3, 6, 16}, writers: 4},
	{ordinal: 92, w: 6, h: 16, encodedLen: 96, opaque: 54, encodedSHA: "26656e6a3e1d4904975db8abfddcefcfd7d16b520eb08c5db458e6e55eb6c413", writesSHA: "fd5207c83a7e63f1ffeae8b1e561276df8916cb0c19fe58b5809d2314bc04e9f", artSHA: "9941464e8109e280301c26a6fdcacce810e9caa93931c547d3cb39de4b2b3806", file: "icons-092.png", artW: 887, artH: 1774, sample: [4]int{138, 197, 737, 1571}, content: [4]int{0, 3, 6, 16}, writers: 4},
	{ordinal: 93, w: 8, h: 16, encodedLen: 122, opaque: 76, encodedSHA: "c0fadddf239b519cf7d15375299b9a5d2c7e4b117251c8fd30f4f0abb37cda4d", writesSHA: "65b4c943ec696d9341da814766248a5002667751ab07ebb7ade07d7f0d7de0d1", artSHA: "c1a16585d2424e742a00bc77824ebbcb54e98b786a99dce7bcd93331a8bf465d", file: "icons-093.png", artW: 887, artH: 1774, sample: [4]int{113, 277, 817, 1581}, content: [4]int{0, 2, 8, 16}, writers: 4},
	{ordinal: 95, w: 8, h: 16, encodedLen: 112, opaque: 66, encodedSHA: "56bbc7d96327a4e4307365ab067264c18ae6283a6ca6e77b395cec59fd760c45", writesSHA: "01b7871fa56a45de351f7fc993ab246a3cfec238eebbcbbd1b4973ec3555105a", artSHA: "8103c8a0a1c837df57c1f31fa6c37ff24203684f3f16315b47218ada3b84232e", file: "icons-095.png", artW: 1086, artH: 1448, sample: [4]int{238, 122, 848, 1328}, content: [4]int{0, 3, 8, 16}, writers: 6},
	{ordinal: 96, w: 7, h: 16, encodedLen: 120, opaque: 75, encodedSHA: "9bea2bc61a7536914be19a4a434f35b01cba37990237e74e774fdaeac3d51644", writesSHA: "0dc550a85c5a8da038b993090fd5815b172f821d081ee6a186fb79313a34a644", artSHA: "1d7d88bc8004429571398c5f58e9528967e9565a1c5e5688a11389a7019e683c", file: "icons-096.png", artW: 887, artH: 1774, sample: [4]int{148, 152, 741, 1589}, content: [4]int{0, 2, 7, 16}, writers: 4},
	{ordinal: 97, w: 7, h: 16, encodedLen: 102, opaque: 61, encodedSHA: "466ef758931ff1f50f388601a0fa2e2c80777940020b09b399591fa66f46a8dd", writesSHA: "ead225167ef7c330ee3f04cfb1396ae2fb387041f00460dc558fbc0ad0361716", artSHA: "fc64e8b372dd064311e6e817a6a5b6bfcfdfc6515c8391e83c5297e5e359a38c", file: "icons-097.png", artW: 887, artH: 1774, sample: [4]int{184, 215, 738, 1566}, content: [4]int{0, 2, 7, 16}, writers: 6},
	{ordinal: 98, w: 6, h: 16, encodedLen: 93, opaque: 50, encodedSHA: "0667b6c059a2ed10dc6a2cee07b6124c7907b896b85c9df550537343e3c01842", writesSHA: "196f8c9353be71fb2840d97f02c923e630ff3c27917f8c8babf0e4229203a59b", artSHA: "5561bf7138e91d27e89698b83431c7dd46bc5708f28b7fc6fe76bf66f26b562d", file: "icons-098.png", artW: 887, artH: 1774, sample: [4]int{195, 354, 712, 1528}, content: [4]int{0, 3, 6, 16}, writers: 4},
	{ordinal: 106, w: 6, h: 16, encodedLen: 96, opaque: 54, encodedSHA: "2d768949596c070cc3b4c3d9c0e75c2fb89d22c2e4506d717725d88e08cbca8b", writesSHA: "e8ed75c9db70a26eeedc9fdd56968ba64ad89bc121eb1c2cc0a5cdb30f331657", artSHA: "dbae8283bf2236b5b69e457f78d278c2df78f640f6a79010f6b0f33314ae8417", file: "icons-106.png", artW: 887, artH: 1774, sample: [4]int{195, 258, 691, 1632}, content: [4]int{0, 3, 6, 16}, writers: 4},
	{ordinal: 107, w: 8, h: 16, encodedLen: 97, opaque: 60, encodedSHA: "1ece271b711847287707fa13cac479b2e0c372157c0dcd71b0e8cd018cd9f5ef", writesSHA: "ec80f48d9d1b78383c699d3f79f7f740cdf2d3f9c40e9b9d88f44faab67fd6b0", artSHA: "fd6afc141275a481ac18631e86dcf0394c56fbdf8b578e83ba3afc360338dc9b", file: "icons-107.png", artW: 887, artH: 1774, sample: [4]int{49, 350, 840, 1594}, content: [4]int{0, 4, 8, 16}, writers: 5},
	{ordinal: 65, w: 14, h: 16, encodedLen: 67, opaque: 33, encodedSHA: "7c93323730b983889829fafff2584d0cf3c0dbab77dd08449363bdc66ae628f7", writesSHA: "6824cd739c3da0b6571fa861ac1cb8736f4f92b63bb614a8b1799e28dc0d781c", artSHA: "c1186be2b4127c33eb7464480c506691a0164a7d331cd18fbc051bc4ca76ce73", file: "icons-065.png", artW: 1254, artH: 1254, sample: [4]int{274, 748, 937, 1017}, content: [4]int{0, 11, 11, 16}, writers: 6},
	{ordinal: 73, w: 7, h: 16, encodedLen: 104, opaque: 58, encodedSHA: "6dd44a10458f2576b555e7f2813ab476ed0a958e36c50150bb2e296aa2410e4d", writesSHA: "c7980d916635aa601778ecd8824adb1e840321629483cc42e02c51deda902a79", artSHA: "76bfd672ac14bbb9a68b81ab893efdf7a675d5c40733efa16d40331635ffe372", file: "icons-073.png", artW: 1254, artH: 1254, sample: [4]int{417, 119, 879, 1136}, content: [4]int{0, 2, 7, 16}, writers: 4},
	{ordinal: 74, w: 8, h: 16, encodedLen: 122, opaque: 68, encodedSHA: "4dcd08e6ac3317bb9052ae3f278fb6c160a99df8a8802bfdcc3b9e9d4b51be99", writesSHA: "f3f329a67adbd08bb87266a6e815313ad731abcc4298ffacc110a78e07422758", artSHA: "74cca71efadd04f8697ba0a6cedec6506cc52eed8a3925c69fce61c2ff1b1e79", file: "icons-074.png", artW: 1254, artH: 1254, sample: [4]int{409, 175, 870, 1080}, content: [4]int{0, 2, 8, 16}, writers: 4},
	{ordinal: 75, w: 13, h: 16, encodedLen: 178, opaque: 102, encodedSHA: "ddfe8dd2a7fe21e6dad85369ae57004af1c7a3bd70007f23d987d00000812f3b", writesSHA: "53c33443de71260a6cc2cb9c4a66cb7be57a13614de0ff789f7b852a07f28d4d", artSHA: "f8861eab6bb9a69be1ea6314b2963978fd8be15ec27a0fc1ddb0f4ee71af2c25", file: "icons-075.png", artW: 1254, artH: 1254, sample: [4]int{261, 214, 1011, 1066}, content: [4]int{0, 1, 13, 16}, writers: 6},
	{ordinal: 76, w: 14, h: 16, encodedLen: 196, opaque: 111, encodedSHA: "0dc0138b6a47a09cd04eda92f057476770b076897045c53d26582fd53ca1b1d4", writesSHA: "b195d762fc715836807b710443c6e7c66864388547dcdb4e8dd9c608b335144c", artSHA: "94a1b242e72c4ef31f1f344e9e9eaca13b430edbd57e6fbdad203370eb691f83", file: "icons-076.png", artW: 1254, artH: 1254, sample: [4]int{224, 177, 1087, 1054}, content: [4]int{0, 1, 14, 16}, writers: 4},
	{ordinal: 77, w: 7, h: 16, encodedLen: 103, opaque: 61, encodedSHA: "4d7d64d2c06ad507408c57c06ef194f4626ed51a12953ee066d95abea5a821a7", writesSHA: "c364a59d89636d3f3d3f4b63bb222f682aa510dc422fbd4efc49db6ac29867d9", artSHA: "6b64925d8335b5f3250e49696da2a9b50d18b0c3d63d31d1b4ef14c1797e31b7", file: "icons-077.png", artW: 1246, artH: 1263, sample: [4]int{425, 161, 854, 1115}, content: [4]int{0, 2, 7, 16}, writers: 6},
	{ordinal: 101, w: 7, h: 16, encodedLen: 104, opaque: 58, encodedSHA: "a4f837747ab45eada75863a64e7176c0a1971aa7deb2d6496b99d25d19c7ad97", writesSHA: "e9606fd87bc489538e26ef7ed6b05d1fc0bf8bcfa2ffaa3cf960f7ea9115cd11", artSHA: "d82df85384a2a6c75d7cb98184e1d593a78346ed55134a32d6a4fbea510bc9f9", file: "icons-101.png", artW: 1254, artH: 1254, sample: [4]int{437, 249, 810, 1048}, content: [4]int{0, 2, 7, 16}, writers: 4},
	{ordinal: 102, w: 8, h: 16, encodedLen: 122, opaque: 69, encodedSHA: "175ca554de4c2d3d305ace60fa648ee304d720299ae96df9adc9ed39548a9f24", writesSHA: "d4007ff1fbf8a06ca121dc978ad0a0e318a2ff1ae9224f67b7ce091c3eaa57e2", artSHA: "dc55590e45ecc9c95f56ba37125612b9a5f814bc7ff17527251a0f6b2129aaaf", file: "icons-102.png", artW: 1254, artH: 1254, sample: [4]int{409, 176, 909, 1081}, content: [4]int{0, 2, 8, 16}, writers: 4},
	{ordinal: 103, w: 13, h: 16, encodedLen: 178, opaque: 102, encodedSHA: "a07203b1e19c6ad9b2afe8ba3f454e834e453bfb8ecb3c8b54a14b8e3be24165", writesSHA: "cc23a9161cc922b84d74b577472322f05ea0c878614785c9de2286fb6196d326", artSHA: "dd0d8180853e005b01d9580fa538e12613fb0cb2f8dd189f85d6345817aa8da1", file: "icons-103.png", artW: 1254, artH: 1254, sample: [4]int{290, 209, 997, 1076}, content: [4]int{0, 1, 13, 16}, writers: 6},
	{ordinal: 104, w: 14, h: 16, encodedLen: 196, opaque: 113, encodedSHA: "f665fba63e6380879b76d8a3e71f19fee2b32c9ec1e9f5072e3ded96f09f5907", writesSHA: "91a113ca50a935b481ad2b6902bbe6c75c515d11800515bf313971aa863fb7c3", artSHA: "44fd32a1b1701a173f23f437bbbbceba4e8087c7f45c644192314902f78f18ba", file: "icons-104.png", artW: 1254, artH: 1254, sample: [4]int{208, 183, 1118, 1097}, content: [4]int{0, 1, 14, 16}, writers: 4},
	{ordinal: 105, w: 7, h: 16, encodedLen: 104, opaque: 61, encodedSHA: "10a9b202d797839cc109e170b1718274428a3d939063773f2236c43058e70c56", writesSHA: "41a4e848421a452fb8fa86187bb0f405eb05da949404f378d202173dfa2b91b4", artSHA: "c586c4f2d047be8fda3b847dca871665e1252bfed3b6030fcf0c655276b2c973", file: "icons-105.png", artW: 1122, artH: 1402, sample: [4]int{360, 174, 770, 1239}, content: [4]int{0, 2, 7, 16}, writers: 4},
	{ordinal: 109, w: 8, h: 16, encodedLen: 124, opaque: 65, encodedSHA: "a0cef918ed3de3b59f74169bb14325421d6fd72873f67219e05475030daa08b1", writesSHA: "9463327c41beb9ecb8478e20bd9d7f1f12c6435d65deede9b4b00b15385954cc", artSHA: "81eee3e5b950fb663133bbdb3950800289972d618257c685181f965c50d46a9f", file: "icons-109.png", artW: 1128, artH: 1394, sample: [4]int{393, 99, 787, 1203}, content: [4]int{1, 1, 7, 16}, writers: 4},
	{ordinal: 110, w: 9, h: 16, encodedLen: 130, opaque: 67, encodedSHA: "3d8452d6e82dc431550cbfd124c1eb69edd9fe94176dc25d0cdb031304da4244", writesSHA: "f9b426a8c5df52a66ecd883f85b6c8b9947139ea89ad3d2a16c8dc1a2fd79b8f", artSHA: "05618744e0295a442dad9a816beb5565fd0173dd2f666a82d1d720b9f84d886e", file: "icons-110.png", artW: 1254, artH: 1254, sample: [4]int{414, 100, 918, 1178}, content: [4]int{1, 1, 9, 16}, writers: 4},
	{ordinal: 111, w: 14, h: 16, encodedLen: 177, opaque: 102, encodedSHA: "0589a87910544b9df69d30b552ad2fad8e2ddaaa2272a0941ca9880dcb58b645", writesSHA: "e9e2f13047dbeb4646c1db3ad69aeb62bec60a9e8ab5dbcfcc502cc42a406a95", artSHA: "b2dd50563f2b1caf610b2f26061c398c54412354e779654e3a50080249046076", file: "icons-111.png", artW: 1254, artH: 1254, sample: [4]int{261, 141, 992, 1061}, content: [4]int{0, 0, 13, 16}, writers: 6},
	{ordinal: 112, w: 14, h: 16, encodedLen: 203, opaque: 117, encodedSHA: "9441bde61ee89f3d0b1a80968ec49d3c6256dc58dcfa967b6f0087585ec1ad16", writesSHA: "b097c2f9958f565ce07359d8b3b298cd70907950f4cf9f53a0ce48233094834f", artSHA: "2610ec1263fd3e534cfb522c25c70f7e6d56cfb485d030bb181dc6677e7aa254", file: "icons-112.png", artW: 1254, artH: 1254, sample: [4]int{249, 183, 965, 1065}, content: [4]int{0, 0, 14, 16}, writers: 4},
	{ordinal: 125, w: 8, h: 16, encodedLen: 127, opaque: 69, encodedSHA: "c9957f171c8c5ace8043272f62fe2f1b86d6da4ecf5dc9cf6520c0737b34261b", writesSHA: "997e5d59ec76bafdc75af5144962ced0ede9b9803c6a5aed015c569bfe0ff4f6", artSHA: "7237926576e6612c297e7359afcc0e3cb47705be6f2b3eda3112d0f0bbfc2dd9", file: "icons-125.png", artW: 1254, artH: 1254, sample: [4]int{390, 124, 864, 1115}, content: [4]int{0, 1, 8, 16}, writers: 4},
	{ordinal: 126, w: 14, h: 16, encodedLen: 201, opaque: 113, encodedSHA: "d71ac1014ffe4052f61e386210bc5a1d86c27200a9151511f5ab79b1e23f1709", writesSHA: "20c99158b4f9c47a8ba1ab3657618851146037fd3fe6cad3739efc511583bbce", artSHA: "b49397ae191453cefb55113049b342779cfb079c4e7028fb37b5cc82174b405c", file: "icons-126.png", artW: 1254, artH: 1254, sample: [4]int{231, 159, 1046, 1099}, content: [4]int{0, 0, 14, 16}, writers: 4},
	{ordinal: 128, w: 8, h: 16, encodedLen: 128, opaque: 72, encodedSHA: "b21111002b447e2ca662416f4c3227c18a3f64ac4adf4950d574d48959dfb9d0", writesSHA: "6ca2778652456d84f1901c27c17bb8eab1dae124fc94a38480f1c798e4831b0c", artSHA: "7056fdc8859c79758cbd41041f4b9f6075e3495a78d09d3db97af8651376680f", file: "icons-128.png", artW: 1254, artH: 1254, sample: [4]int{408, 131, 920, 1124}, content: [4]int{0, 1, 8, 16}, writers: 4},
	{ordinal: 129, w: 14, h: 16, encodedLen: 204, opaque: 115, encodedSHA: "3e4a724489ce7b301b4a95a371dda12688a3ee3739f796511cf8808fc934fb10", writesSHA: "3e73552ec59bb69ecb7fa63f1e439ece8dd5030441439797feee4de800d48c90", artSHA: "fb55e840e9a47eebda26348b2ce1c08f935227c32a32a17b86d49def1e8968af", file: "icons-129.png", artW: 1254, artH: 1254, sample: [4]int{239, 201, 1035, 1076}, content: [4]int{0, 0, 14, 16}, writers: 4},
	{ordinal: 3, w: 21, h: 16, encodedLen: 271, opaque: 176, encodedSHA: "93f047dadde245c823f403712643a6277a4e6850914e60fe597d956e928d5798", writesSHA: "9e1702350e126520268c102c32efae27846e55bbef45e40c7ddedd335da21873", artSHA: "98e35a733d1741b3d14ae7dace783d5eafedf0aff89afae05fe1ede6878a3c5b", file: "icons-003.png", artW: 1437, artH: 1095, sample: [4]int{107, 80, 1362, 1065}, content: [4]int{2, 0, 20, 15}, writers: 7, scaled100: true, nominal: [2]uint16{15, 20}},
	{ordinal: 11, w: 21, h: 16, encodedLen: 175, opaque: 152, encodedSHA: "2104209ba40bb60e18d20e3b86dd01e8e280b7f7287cde3e2e259553ec326a14", writesSHA: "f5fa908a9476592599d912c7b38134a15902f1ec870323fbb82682fa61957d85", artSHA: "858d4962dba4b24075dca0bc2c3845ef8c0d8af2537bea5137f02554a4060044", file: "icons-011.png", artW: 1437, artH: 1095, sample: [4]int{147, 220, 1302, 935}, content: [4]int{2, 3, 19, 14}, writers: 6, scaled100: true, nominal: [2]uint16{37, 142}},
	{ordinal: 118, w: 6, h: 5, encodedLen: 30, opaque: 15, encodedSHA: "9e7150813c824ad38e12ddb7924f76fc6fc9d9fed724f63ca1e4162d24664f8f", writesSHA: "0da25d4e0ec7aee32db5e4cae1385985b3b36b690eb6acd2b93b208ca5225fc5", artSHA: "0a447fb0f0381c35b4598aec52daf36bb3f2e4bfea3075500e26c98879d9a22a", file: "icons-118.png", artW: 1374, artH: 1145, sample: [4]int{253, 202, 1120, 934}, content: [4]int{1, 0, 6, 4}, writers: 6, scaled100: true, nominal: [2]uint16{30, 84}},
	{ordinal: 113, w: 16, h: 16, encodedLen: 247, opaque: 226, encodedSHA: "6986a798dfe12fa00ea605716f038eb282feaab79c3c565efeefa66af107f75f", writesSHA: "6dc354df0cfee9ea5690506d53fceaeefd271840b904f7470a199a3409fcdc4a", artSHA: "7e6c49b20af1e32e3f031775a79e2568ad72e2e7b9086f31e59d365bf1c81a78", file: "icons-113.png", artW: 1254, artH: 1254, sample: [4]int{220, 135, 1100, 1140}, content: [4]int{0, 0, 16, 16}, writers: 7, paletteSHA: "0b1205c4c138976acab792e6bf5458765357acab29a818303ddc0227858c11aa", paletteIndices: []byte{45, 47, 82, 83, 84, 85, 86, 113, 114, 115, 116, 117, 118, 119, 128, 129, 130, 132, 134, 136, 137, 138}},
	{ordinal: 0, w: 21, h: 16, encodedLen: 340, opaque: 266, encodedSHA: "17dfcc99e48d952ef8e30b239c470521423a0e244210f30118ad8078369d4c2f", writesSHA: "aa31f395e158d7be9155976d788390b2faae7f555896c1ce0c0e932975870882", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{29, 58, 294, 274}, content: [4]int{0, 0, 21, 16}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{15, 95}},
	{ordinal: 1, w: 21, h: 16, encodedLen: 333, opaque: 288, encodedSHA: "38fae9ec6627c827910c0ec6b51057e6bf3b09b0d31a1d08ae430326e072a0c0", writesSHA: "3ba8b8e2bc9642cc6bded70f8f610261d70f731f653e650daa5a5bb22452f912", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{338, 59, 606, 274}, content: [4]int{0, 0, 21, 16}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{37, 78}},
	{ordinal: 2, w: 21, h: 16, encodedLen: 330, opaque: 291, encodedSHA: "d423674756278d69b84336503db56233c07528447c78270fd02c4cf5a9dcfc6f", writesSHA: "4f51cdb9c99e58ca36fade60123365171ccb981a81d5fbbf0147ac56618095ad", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{651, 59, 926, 274}, content: [4]int{0, 0, 21, 16}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{15, 78}},
	{ordinal: 10, w: 21, h: 16, encodedLen: 211, opaque: 129, encodedSHA: "900912c8ff3cca6e03fe851d44ed5a2c60bd2a2b92b02e5b3127429eac896e97", writesSHA: "e0a3e9c309778fc71309cf4772ae0bce663d7a6848b99b83739a744a21aa89ab", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{982, 85, 1214, 255}, content: [4]int{2, 1, 19, 13}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{15, 142}},
	{ordinal: 12, w: 21, h: 16, encodedLen: 205, opaque: 158, encodedSHA: "31faaf69a0876e176f4c51783d20da949d826544b60128f044b79929ebb365ef", writesSHA: "f9dfe6eb888d1ec15a7922432132095e0d14dfc22b5183984822c411df1ad4b8", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{37, 401, 287, 575}, content: [4]int{2, 3, 20, 14}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{59, 142}},
	{ordinal: 13, w: 21, h: 16, encodedLen: 257, opaque: 222, encodedSHA: "9efb8995a16e7caefbc92a0e15776d62ac102197cb1fb1bb28de3d57945c3053", writesSHA: "2ad8f2ee1423d1ea35ae810e2872f7568fd97c051287ac0eb458986192fc0e64", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{338, 391, 615, 578}, content: [4]int{0, 2, 21, 15}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{81, 142}},
	{ordinal: 17, w: 16, h: 16, encodedLen: 102, opaque: 49, encodedSHA: "c02f5dd257ea8b0977b49f255d85341b72ce462a2b3e07a0aa1acc828488a0ad", writesSHA: "027e2bc6aa938410f05e86784df49d742ecad454e280670dad1332bb39f0a9b8", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{708, 413, 859, 569}, content: [4]int{4, 4, 13, 13}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{130, 181}},
	{ordinal: 18, w: 16, h: 16, encodedLen: 107, opaque: 60, encodedSHA: "a24cf8d30c1a0be4c07789abd22c9394cf3e3b37261ca58c7ab1f48dca05518b", writesSHA: "6eca11804a01eeaf1c1168376a5a62540da22bd270deb444bd051093656ca8d8", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{974, 351, 1220, 598}, content: [4]int{0, 0, 16, 16}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{13, 181}},
	{ordinal: 19, w: 8, h: 8, encodedLen: 51, opaque: 28, encodedSHA: "84851884d43f546d7877758a528688e58e44e72a5288e809cb5ebad9babfa3e8", writesSHA: "85652fbb36c52dd82542f13f8c90970b58294cc6480b7cd972176df267d5519a", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{80, 721, 238, 868}, content: [4]int{0, 0, 8, 8}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{28, 173}},
	{ordinal: 20, w: 4, h: 4, encodedLen: 21, opaque: 12, encodedSHA: "b2f0a233ea14d88f9cd0e15924f6bfb99868f2039c7ad7dc1e79b70a0f56f79a", writesSHA: "835873520c12fb76874d946f8fe9cace7e241e56a43ddb5431642c9e4519d719", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{430, 749, 512, 832}, content: [4]int{0, 0, 4, 4}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{37, 169}},
	{ordinal: 21, w: 2, h: 2, encodedLen: 9, opaque: 4, encodedSHA: "e79d8d1c47a36a6ffef2f22a371fa710f3895ee43f7c9cfd83a92d553c4544d8", writesSHA: "14e23838345fdadc32058c5753bf4bb751dd0472ae42d87fa751812dab738601", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{765, 772, 806, 811}, content: [4]int{0, 0, 2, 2}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{43, 167}},
	{ordinal: 39, w: 8, h: 12, encodedLen: 98, opaque: 54, encodedSHA: "cdef5dc5d6bc9cf663da5e8c472728c4ffd8f76f8e1a8584107460baf0fc2c62", writesSHA: "a2515f6cc13ceeed38d1f736f1149e1478069f7d255b1ab56a3d36199833d7e5", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{1013, 660, 1181, 911}, content: [4]int{0, 0, 8, 12}, writers: 7},
	{ordinal: 40, w: 8, h: 12, encodedLen: 103, opaque: 65, encodedSHA: "b89d52b909c3d3b6fdf86c1589799f1761fab0f27bcdf20e74a903edf0b6c42a", writesSHA: "0d18963fc2f524ba9a3d0de496ebc02f14966907e79abca3fe7d413acd080f5e", artSHA: "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", file: "icons-remaining-1.png", artW: 1254, artH: 1254, sample: [4]int{75, 978, 248, 1234}, content: [4]int{0, 0, 8, 12}, writers: 7},
	{ordinal: 41, w: 10, h: 12, encodedLen: 102, opaque: 63, encodedSHA: "60bcb3023b6a5b6d074a883e95a9403961302bf9628be0a7cd2c614a2e424f62", writesSHA: "8d22f7d76d4cff4028c9ef8702bd109715c1e0e24eea5c0e48d8341308595269", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{49, 71, 283, 291}, content: [4]int{0, 1, 10, 11}, writers: 7},
	{ordinal: 43, w: 10, h: 12, encodedLen: 52, opaque: 44, encodedSHA: "5d10c51e34663ab682895829cf5aa1528a95d8ff3bbd374acd11fc8c7dce6e54", writesSHA: "bc56df81b4085b3a4f14232c81b6b7778e66f345ff353544aab52d80009864d8", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{350, 119, 593, 236}, content: [4]int{0, 3, 10, 8}, writers: 7},
	{ordinal: 44, w: 10, h: 12, encodedLen: 97, opaque: 75, encodedSHA: "ee8fb7d099ef7c9e0b506f97f27337b45d3a40879b954927365a7573559783d2", writesSHA: "3aa4c303b4f4c3d4908ae7b49a0d9e1c9d6323a6c221ab9c2e5e19380c6ec42b", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{666, 90, 898, 283}, content: [4]int{0, 2, 10, 11}, writers: 7},
	{ordinal: 45, w: 10, h: 12, encodedLen: 63, opaque: 40, encodedSHA: "e3d4d2b190e4b9be6cf86aa2bbf479153b1d37074eea523cbb69f8e3c6a51576", writesSHA: "908286f29dec706b949dd437690f1f154cb202110970e26d0c6c44aad8c7bad8", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{979, 119, 1212, 252}, content: [4]int{0, 3, 10, 9}, writers: 7},
	{ordinal: 46, w: 13, h: 12, encodedLen: 147, opaque: 104, encodedSHA: "d154cca85e5cd024121753e95ecddc9a28652729633501f6bd2dcb2be703455a", writesSHA: "7a7b293da7eec5040a03b8b39f550a3e0fb7200554d553837569da4b77503c43", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{27, 353, 310, 606}, content: [4]int{0, 0, 13, 12}, writers: 7},
	{ordinal: 47, w: 7, h: 12, encodedLen: 94, opaque: 64, encodedSHA: "4947baaa5f9952ba826c3c695cdd9db089b5aafeed62f4eed1248524f53bcfeb", writesSHA: "d41c413f90b2de77b46a99f822c152687c136fafe38bde5fa86cade299435331", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{390, 364, 556, 606}, content: [4]int{0, 1, 7, 12}, writers: 7},
	{ordinal: 48, w: 9, h: 12, encodedLen: 103, opaque: 44, encodedSHA: "8e1bba1c79ae7519aff52d58ff31dc426cadb020a3709390719092cf519daa54", writesSHA: "98acd974405611c17a24e2ed23775953bd7b283a4c1fab2edcea12af5abf5871", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{744, 349, 830, 610}, content: [4]int{3, 0, 7, 12}, writers: 7},
	{ordinal: 49, w: 8, h: 12, encodedLen: 97, opaque: 68, encodedSHA: "ed8c46d41dad94dec9b889a3e3ac8f0612ebe9985c256a6bb8e23be301ec2951", writesSHA: "36c8bf836ad69bd7b68dce038754dff0b44ddd73c01cfa657023a89ddf6fd3ff", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{1006, 364, 1186, 606}, content: [4]int{0, 1, 8, 12}, writers: 7},
	{ordinal: 50, w: 8, h: 12, encodedLen: 108, opaque: 80, encodedSHA: "e35f6cf1189341eccf90be33170e1d670f599be55097f2e9a57dde95d5b60096", writesSHA: "112868802c9923091b71ffb4bce315e29303743e8eab11ca4f19817dafae8ba4", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{59, 651, 257, 916}, content: [4]int{0, 0, 8, 12}, writers: 7},
	{ordinal: 51, w: 9, h: 12, encodedLen: 82, opaque: 55, encodedSHA: "94b3c760ac2f4783348119cad6bf84dc12668967cbd71a5e739f01617ad50ec7", writesSHA: "ed782221dc331b6dff130d46ce86af06a8cefbe093dff609be52cd4afe7bc2b6", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{365, 701, 577, 883}, content: [4]int{0, 2, 9, 10}, writers: 7},
	{ordinal: 52, w: 9, h: 12, encodedLen: 76, opaque: 38, encodedSHA: "8431cbf11db2980ef56331f8b2b928d8fb65e57838dfbb090773ab9d86d7534f", writesSHA: "6461104314a6642718f37926bac37f8fe1e5ef35bf2569f25b8956ee59c8c7b0", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{667, 688, 889, 899}, content: [4]int{0, 2, 9, 11}, writers: 7},
	{ordinal: 55, w: 8, h: 12, encodedLen: 74, opaque: 39, encodedSHA: "befe960a146abe4ace659fbbe52cba6aa414b4c4dbb06d23f1b4b81ba8994e07", writesSHA: "3fb67f713bf0651f8a139aa25b5db9616603d98fadc23af914d52b8f49cd0a26", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{996, 694, 1192, 884}, content: [4]int{0, 2, 8, 10}, writers: 7},
	{ordinal: 57, w: 7, h: 12, encodedLen: 95, opaque: 52, encodedSHA: "1c1f2f6ab1086839a2bc260b1a3d1051b177c96b4ca5e9e342c3c8e65a6a2d78", writesSHA: "12f04c038edfc0283f5ef150823eafd478d05b6bce314e21a3ddcfb7ec962a39", artSHA: "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", file: "icons-remaining-2.png", artW: 1254, artH: 1254, sample: [4]int{85, 977, 228, 1214}, content: [4]int{0, 0, 7, 12}, writers: 7},
	{ordinal: 61, w: 6, h: 16, encodedLen: 103, opaque: 60, encodedSHA: "0eb0d4577e61914cec86c89dcd62a841beeac508bd1062f278e7990cba5d9bc1", writesSHA: "3ae5c90acba5127051174762d48328ca6fcb20e7a45893f8757aacaca08da6c0", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{104, 59, 227, 313}, content: [4]int{0, 2, 6, 16}, writers: 7},
	{ordinal: 63, w: 16, h: 16, encodedLen: 107, opaque: 60, encodedSHA: "e879c6f279ad1a9fff064160c527a4dafb521cd837e68c82d428ee6120ecbcf0", writesSHA: "8853871614318fd825e7fee01ecdd786e581911be798dd5f368c3c4a717b824c", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{377, 68, 594, 306}, content: [4]int{0, 0, 16, 16}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{56, 181}},
	{ordinal: 64, w: 16, h: 16, encodedLen: 121, opaque: 35, encodedSHA: "599dcd92bc3a7c0590e3872907429db5dc7fe21065142b1681153fd0efbb1c2f", writesSHA: "9a86c21ff468ad0a2a12fff4023ba87b1dfbbc07f4ca6f1d45a5c15261d4aaba", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{681, 86, 880, 291}, content: [4]int{2, 2, 13, 13}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{73, 181}},
	{ordinal: 99, w: 7, h: 16, encodedLen: 95, opaque: 55, encodedSHA: "a8bb86f121b99605e81776d3dfcbe36da011ed44885595a3e070f5f0024bb230", writesSHA: "13fe50097ef86c2e9d4c0ced47bcd4ec76e568fa1a0bff587088ca6fc7fd096e", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{1024, 86, 1158, 313}, content: [4]int{0, 3, 7, 16}, writers: 7},
	{ordinal: 108, w: 8, h: 16, encodedLen: 124, opaque: 56, encodedSHA: "58fc14eacbe70dfa826ffbcc098c132d908e59c55148ea069f01e8c2be636f01", writesSHA: "286ac78f5b6d52fb985587ed94cabf2dc0c8aafe73fc03cc4120aa4ed3e82904", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{100, 313, 237, 627}, content: [4]int{0, 0, 8, 16}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{98, 95}},
	{ordinal: 114, w: 16, h: 16, encodedLen: 246, opaque: 226, encodedSHA: "ad2c47fa6834acda2c0862a70948c58f78ed2c410dc87de9746fc7808f69ea0b", writesSHA: "6a0ad0ae58c199d57ded546b7fbda5d823f66c6a2fed3c1a43ae4c5a62ce4d30", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{366, 390, 588, 625}, content: [4]int{0, 0, 16, 16}, writers: 7, paletteSHA: "0b1205c4c138976acab792e6bf5458765357acab29a818303ddc0227858c11aa", paletteIndices: []byte{45, 47, 82, 83, 84, 85, 86, 113, 114, 115, 116, 117, 118, 119, 128, 129, 130, 132, 134, 136, 137, 138}},
	{ordinal: 115, w: 16, h: 16, encodedLen: 244, opaque: 226, encodedSHA: "bc2468e9cf3f2c049c47b8f2bbf042e2d6628a5dcfba726436331aecdc1bfcdd", writesSHA: "4058f1c297f73c012d847824c060f2646a72cb40e9a9f3679406f23f7ef9c883", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{676, 390, 899, 625}, content: [4]int{0, 0, 16, 16}, writers: 7, paletteSHA: "0b1205c4c138976acab792e6bf5458765357acab29a818303ddc0227858c11aa", paletteIndices: []byte{45, 47, 82, 83, 84, 85, 86, 113, 114, 115, 116, 117, 118, 119, 128, 129, 130, 132, 134, 136, 137, 138}},
	{ordinal: 116, w: 16, h: 16, encodedLen: 246, opaque: 226, encodedSHA: "33ac150455e773dd44f0fe68d87ffa25ff592f7c0688b506748f69daeac56221", writesSHA: "429124e3ed1bda60269cbe18a5e86da0608c813448f0581fd2f277fa5d04d63c", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{989, 313, 1212, 625}, content: [4]int{0, 0, 16, 16}, writers: 7, paletteSHA: "0b1205c4c138976acab792e6bf5458765357acab29a818303ddc0227858c11aa", paletteIndices: []byte{45, 47, 82, 83, 84, 85, 86, 113, 114, 115, 116, 117, 118, 119, 128, 129, 130, 132, 134, 136, 137, 138}},
	{ordinal: 117, w: 16, h: 16, encodedLen: 243, opaque: 226, encodedSHA: "f8bab9e5d3fe0956865f62402b463434c3dc1ff3b232dfa06280fd3bd427f299", writesSHA: "6db5838c37de67f7027c86dd43203246d2a3cc75d935135d411ddaec2a84b4bb", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{57, 627, 280, 914}, content: [4]int{0, 0, 16, 16}, writers: 7, paletteSHA: "0b1205c4c138976acab792e6bf5458765357acab29a818303ddc0227858c11aa", paletteIndices: []byte{45, 47, 82, 83, 84, 85, 86, 113, 114, 115, 116, 117, 118, 119, 128, 129, 130, 132, 134, 136, 137, 138}},
	{ordinal: 119, w: 6, h: 5, encodedLen: 30, opaque: 15, encodedSHA: "37e26754fbc8a6634ac9e3a2377b6a68aafa29cba182893a10f28256b41f2414", writesSHA: "d951386c9f1b2f904aeef4dd96c36d378324d3f036984d9c734d2e5aed23b468", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{419, 718, 563, 860}, content: [4]int{1, 0, 6, 4}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{30, 90}},
	{ordinal: 120, w: 6, h: 5, encodedLen: 30, opaque: 15, encodedSHA: "86f00b994e7ab29721ca5a4ff6d1c177c3dceb9c52057018d1450202a6fb2aa1", writesSHA: "54b6c3995d42fee92ea9504a666098dad1557cc54ea926b2d6c3ce69fd6195e0", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{729, 717, 870, 860}, content: [4]int{1, 0, 6, 4}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{37, 90}},
	{ordinal: 121, w: 6, h: 5, encodedLen: 30, opaque: 15, encodedSHA: "357fb641980e3bbe4a6dec11e0e46719ec26d2a12146648607e30efadc5f358b", writesSHA: "88b4f7db9857a1668c46d8bff34167221a47cdc1f15c501e31f7fcf33648010d", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{1041, 717, 1189, 860}, content: [4]int{1, 0, 6, 4}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{37, 84}},
	{ordinal: 130, w: 6, h: 5, encodedLen: 31, opaque: 15, encodedSHA: "6e379a7113c4f357081fc4f2f5147a09ed99ed0fec53034cbe17c9038e23ba64", writesSHA: "538a3d9ce3ad0de09a98eae55193689e53087f5e346e823360ee84902116e813", artSHA: "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", file: "icons-remaining-3.png", artW: 1254, artH: 1254, sample: [4]int{98, 1008, 244, 1139}, content: [4]int{1, 0, 6, 4}, writers: 7, scaled100: true, alsoPlain: true, nominal: [2]uint16{44, 84}},
}
var hdSmallWriterCodes = map[uint16][]byte{
	0x181: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x02, 0xeb, 0xe7, 0xeb, 0xd0, 0x3b},
	0x1b4: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x03, 0xeb, 0xe7, 0x90, 0xeb, 0xcc},
	0x1d2: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xeb, 0xb5, 0x90, 0x5a, 0x5b, 0x03, 0x5e, 0xfe, 0x79},
}

type hdSmallCell struct {
	owned  bool
	local  uint32
	native byte
	slot   uint16
}
type hdSmallPending struct {
	cell       hdSmallCell
	old, value byte
	cursor     int
}
type hdSmallRuntime struct {
	stage                                     [64000]hdSmallCell
	destination                               uint32
	scaledActive                              bool
	sourceDS                                  uint16
	sourceOffset                              int
	backing                                   map[uint32]hdSmallCell
	bufferSaves, bufferRestores, peakBuffered uint64
	h                                         *hdRuntime
	frames                                    []hdSmallFrame
	visible                                   [64000]hdSmallCell
	pending                                   map[int]hdSmallPending
	active, outside                           bool
	selected                                  int
	x, y                                      int
	sp, retCS, retIP                          uint16
	start, revision, accepted, rejected       uint64
	writes                                    [336]byte
	counts                                    [336]uint16
	trace                                     bool
	calls, pairs                              []map[string]any
	entry                                     map[string]any
}

func hdSmallRead(path, want string, limit int64) ([]byte, error) {
	raw, err := hdReadFile(path, limit)
	if err != nil {
		return nil, err
	}
	if hash(raw) != want {
		return nil, fmt.Errorf("小圖像指紋不同：%s", path)
	}
	return raw, nil
}
func loadHDSmallRuntime(h *hdRuntime, game, directory string) (*hdSmallRuntime, error) {
	if h == nil || directory == "" {
		return nil, fmt.Errorf("小圖像正式層需要既有HD及素材目錄")
	}
	if _, err := hdSmallRead(filepath.Join(game, "ICONS.SS"), "a8a21f052d2e6c9ede34a6cb254b05f2036322031f7ab0ccb0859adf9b6e0716", 8<<20); err != nil {
		return nil, err
	}
	p := &hdSmallRuntime{h: h, frames: append([]hdSmallFrame(nil), hdSmallFrames...), pending: map[int]hdSmallPending{}, backing: map[uint32]hdSmallCell{}}
	for i := range p.frames {
		f := &p.frames[i]
		if f.file == "" {
			continue
		}
		raw, err := hdSmallRead(filepath.Join(directory, f.file), f.artSHA, 8<<20)
		if err != nil {
			return nil, err
		}
		c, err := png.DecodeConfig(bytes.NewReader(raw))
		if err != nil || c.Width != f.artW || c.Height != f.artH {
			return nil, fmt.Errorf("小圖像原圖尺寸不同：%d", f.ordinal)
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		a, b := f.sample, f.content
		if a[0] < 0 || a[1] < 0 || a[2] <= a[0] || a[3] <= a[1] || a[2] > f.artW || a[3] > f.artH || b[0] < 0 || b[1] < 0 || b[2] <= b[0] || b[3] <= b[1] || b[2] > f.w || b[3] > f.h {
			return nil, fmt.Errorf("小圖像取樣邊界不同：%d", f.ordinal)
		}
		f.art = image.NewRGBA(image.Rect(0, 0, f.w*4, f.h*4))
		for y := b[1] * 4; y < b[3]*4; y++ {
			for x := b[0] * 4; x < b[2]*4; x++ {
				sx := a[0] + (2*(x-b[0]*4)+1)*(a[2]-a[0])/((b[2]-b[0])*8)
				sy := a[1] + (2*(y-b[1]*4)+1)*(a[3]-a[1])/((b[3]-b[1])*8)
				f.art.Set(x, y, im.At(sx, sy))
			}
		}
	}
	h.m.WatchWrite(0, 0x9ffff, func(_ *golem.Machine, a uint32, o, v byte) { p.memoryWrite(a, o, v) })
	return p, nil
}
func (p *hdSmallRuntime) beforeInstruction() {
	if p == nil {
		return
	}
	m, c := p.h.m, p.h.m.CPU
	if p.active {
		adjust := uint16(10)
		if p.scaledActive {
			adjust = 12
		}
		if c.Seg[golem.CS] == p.retCS && c.IP == p.retIP && c.R[golem.SP] == p.sp+adjust {
			p.finish()
		} else if m.Steps-p.start > 100000 || (c.Seg[golem.CS] == 0xd46 && c.IP == 0xa) || (c.Seg[golem.CS] == 0xd66 && c.IP == 4) {
			p.active = false
			p.rejected++
			p.frames[p.selected].rejected++
		}
	}
	plain := c.Seg[golem.CS] == 0xd46 && c.IP == 0xa
	scaled := c.Seg[golem.CS] == 0xd66 && c.IP == 4
	if p.active || (!plain && !scaled) {
		return
	}
	pc := int(c.Seg[golem.CS])*16 + int(c.IP)
	code := []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}
	if scaled {
		code = []byte{0xc8, 0x6e, 1, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}
	}
	if !bytes.Equal(m.Mem[pc:pc+12], code) {
		return
	}
	slot := -1
	for i, f := range p.frames {
		if (f.scaled100 == scaled || (f.alsoPlain && !scaled)) && c.R[golem.AX] == uint16(f.ordinal+1) {
			slot = i
			break
		}
	}
	if slot < 0 {
		return
	}
	f := &p.frames[slot]
	count := 5
	if scaled {
		count = 6
	}
	words, ok := hdBuildingWords(m.Mem, c.Seg[golem.SS], c.R[golem.SP], count)
	if !ok {
		return
	}
	off := int(words[count-2]) + 0x36 + int(c.R[golem.AX]&0x7fff)*12
	if off+12 > 65536 {
		return
	}
	record, ok := hdBuildingWords(m.Mem, words[count-1], uint16(off), 6)
	if !ok {
		return
	}
	source := int(record[1])*16 + int(record[0])
	if int(record[0])+f.encodedLen > 65536 || source+f.encodedLen > len(m.Mem) || hash(m.Mem[source:source+f.encodedLen]) != f.encodedSHA {
		return
	}
	d, ok := hdBuildingWords(m.Mem, c.Seg[golem.DS], c.R[golem.BX], 4)
	if !ok {
		return
	}
	destination := uint32(d[3])*16 + uint32(d[2])
	x, y := int(int16(c.R[golem.DX])), int(int16(words[2]))
	validSurface := d[0] == 200 && d[1] == 320 && d[2] == 0 && d[3] == 0x2cae
	if scaled {
		x -= f.w / 2
		y = int(int16(words[3])) - f.h + 1
		validSurface = d[0] == 200 && d[1] == 320 && d[2] == 0 && (d[3] == 0x3c50 || (d[3] == 0x2cae && f.ordinal != 11)) && words[2] == 100 && record[2] == f.nominal[0] && record[3] == f.nominal[1]
	}
	if !validSurface || int(record[4]) != f.w || int(record[5]) != f.h || x < 0 || x+f.w > 320 || y < 0 || y+f.h > 200 {
		p.rejected++
		f.rejected++
		return
	}
	p.selected, p.active, p.outside, p.x, p.y = slot, true, false, x, y
	p.destination = destination
	p.scaledActive = scaled
	p.sourceDS, p.sourceOffset = record[1], int(record[0])
	p.start, p.sp, p.retCS, p.retIP = m.Steps, c.R[golem.SP], words[1], words[0]
	p.writes, p.counts = [336]byte{}, [336]uint16{}
	if p.trace {
		decoder := "D46"
		if scaled {
			decoder = "D66"
		}
		p.entry = map[string]any{"ordinal": f.ordinal, "decoder": decoder, "destination": destination, "entry_step": m.Steps, "registers": c.R, "segments": c.Seg, "stack": words, "record_far": fmt.Sprintf("%04X:%04X", words[count-1], off), "record": record, "source_far": fmt.Sprintf("%04X:%04X", record[1], record[0]), "source_sha256": hash(m.Mem[source : source+f.encodedLen]), "rect": [4]int{x, y, x + f.w, y + f.h}}
	}
}
func (p *hdSmallRuntime) finish() {
	p.active = false
	f := &p.frames[p.selected]
	var encoded []byte
	for k, n := range p.counts[:f.w*f.h] {
		if n == 0 {
			continue
		}
		if n != 1 {
			p.outside = true
		}
		encoded = binary.LittleEndian.AppendUint16(encoded, uint16(k))
		encoded = append(encoded, p.writes[k])
	}
	if p.outside || len(encoded) != f.opaque*3 || hash(encoded) != f.writesSHA {
		p.rejected++
		f.rejected++
		return
	}
	for k, n := range p.counts[:f.w*f.h] {
		if n == 1 {
			i := (p.y+k/f.w)*320 + p.x + k%f.w
			cell := hdSmallCell{true, uint32(k), p.writes[k], uint16(p.selected)}
			if p.destination == hdSeaStage {
				p.stage[i] = cell
			} else {
				p.visible[i] = cell
			}
		}
	}
	p.accepted++
	f.accepted++
	if p.trace {
		if len(p.calls) >= 20000 {
			panic("小圖像繪製紀錄超限")
		}
		p.entry["return_step"] = p.h.m.Steps
		p.entry["return_registers"] = p.h.m.CPU.R
		p.entry["return_segments"] = p.h.m.CPU.Seg
		p.entry["return_ip"] = p.h.m.CPU.IP
		p.entry["writes_sha256"] = hash(encoded)
		p.calls = append(p.calls, p.entry)
		p.entry = nil
	}
}
func (p *hdSmallRuntime) write(addr uint32, old, value byte) {
	m := p.h.m
	i := int(addr - hdBuildingCanvas)
	p.revision++
	cs, ip := m.CPU.OpAddr()
	p.recordActiveWrite(addr, value)

	if cs == 0xb68 && ip == 0x51c && m.CPU.Seg[golem.DS] == 0xa000 && m.CPU.Seg[golem.ES] == 0x2cae {
		pc := int(cs)*16 + int(ip)
		if bytes.Equal(m.Mem[pc:pc+16], []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}) {
			dest := int(m.CPU.Seg[golem.ES])*16 + int(m.CPU.R[golem.DI])
			source := int(m.CPU.R[golem.SI]) + int(addr) - dest
			if _, ok := p.h.cursorSource(); ok && source >= 0xfa00 && source < 0xfc00 && m.Mem[0xa0000+source] == value {
				k := source & 255
				if source >= 0xfb00 {
					p.pending[i] = hdSmallPending{p.visible[i], old, value, k}
					if p.visible[i].owned {
						p.frames[p.visible[i].slot].paints++
					}
					p.visible[i].owned = false
					return
				}
				prior, ok := p.pending[i]
				delete(p.pending, i)
				if ok && prior.cursor == k && old == prior.value && value == prior.old {
					p.visible[i] = prior.cell
					if prior.cell.owned {
						f := &p.frames[prior.cell.slot]
						f.restores++
						if p.trace {
							if len(p.pairs) >= 200000 {
								panic("小圖像游標紀錄超限")
							}
							p.pairs = append(p.pairs, map[string]any{"ordinal": f.ordinal, "step": m.Steps, "linear": addr, "source_cursor_index": k, "native": prior.cell.native, "local": prior.cell.local, "paint_old": prior.old, "paint_value": prior.value, "restore_old": old, "restore_value": value, "registers": m.CPU.R, "segments": m.CPU.Seg, "code16": fmt.Sprintf("%x", m.Mem[pc:pc+16])})
						}
					}
					return
				}
			}
		}
	}
	cell, src, ok := p.copySource(addr, value)
	p.visible[i].owned = false
	clear(p.pending)
	if ok && (src < int(hdBuildingCanvas) || src >= int(hdBuildingCanvas)+64000) {
		p.visible[i] = cell
		p.bufferRestores++
		p.frames[cell.slot].bufferRestores++
	}
}
func (p *hdSmallRuntime) receipt(f draftNativeFrame) map[string]any {
	if p == nil {
		return nil
	}
	owned, valid := 0, 0
	mask := make([]byte, 8000)
	counts := make([][2]int, len(p.frames))
	masks := make([][]byte, len(p.frames))
	for i := range masks {
		masks[i] = make([]byte, 8000)
	}
	for i, c := range p.visible {
		if !c.owned || int(c.slot) >= len(p.frames) {
			continue
		}
		owned++
		counts[c.slot][0]++
		if f.canvas[i] == c.native {
			valid++
			counts[c.slot][1]++
			mask[i>>3] |= 1 << uint(i&7)
			masks[c.slot][i>>3] |= 1 << uint(i&7)
		}
	}
	sources := map[string]any{}
	for i, a := range p.frames {
		sources[fmt.Sprint(a.ordinal)] = map[string]any{"ordinal": a.ordinal, "owned": counts[i][0], "valid": counts[i][1], "mask": masks[i], "accepted": a.accepted, "rejected": a.rejected, "cursor_paint_points": a.paints, "cursor_restore_points": a.restores, "buffer_saves": a.bufferSaves, "buffer_restores": a.bufferRestores, "art_available": a.art != nil, "painted": 0, "alpha_pixels": 0}
	}
	return map[string]any{"formal": true, "asset": "small-images", "accepted": p.accepted, "rejected": p.rejected, "owned": owned, "valid": valid, "mask": mask, "sources": sources, "pending": len(p.pending), "buffer_saves": p.bufferSaves, "buffer_restores": p.bufferRestores, "buffered": len(p.backing), "peak_buffered": p.peakBuffered, "revision": p.revision}
}
func (p *hdSmallRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	if p == nil {
		return nil
	}
	receipt := p.receipt(f)
	sources := receipt["sources"].(map[string]any)
	painted, alpha := 0, 0
	for i, c := range p.visible {
		if !c.owned || int(c.slot) >= len(p.frames) || f.canvas[i] != c.native {
			continue
		}
		a := p.frames[c.slot]
		if a.art == nil || !a.paletteSupported(f.palette) || (a.scaled100 && !hdSmallScaledPaletteSupported(f.palette)) {
			continue
		}
		sx, sy := int(c.local)%a.w*4, int(c.local)/a.w*4
		ink := 0
		for y := 0; y < 4; y++ {
			for x := 0; x < 4; x++ {
				_, _, _, v := a.art.At(sx+x, sy+y).RGBA()
				if v != 0 {
					ink++
				}
			}
		}
		if ink == 0 {
			continue
		}
		x, y := i%320*4, i/320*4
		draw.Draw(out, image.Rect(x, y, x+4, y+4), a.art, image.Pt(sx, sy), draw.Over)
		painted++
		alpha += ink
		r := sources[fmt.Sprint(a.ordinal)].(map[string]any)
		r["painted"] = r["painted"].(int) + 1
		r["alpha_pixels"] = r["alpha_pixels"].(int) + ink
	}
	receipt["painted"], receipt["alpha_pixels"] = painted, alpha
	return receipt
}

// R51已驗的主畫布保存／還原。單一群組觀測器，不接受RAM至RAM或暫存畫布。
func (p *hdSmallRuntime) memoryWrite(addr uint32, old, value byte) {
	if addr >= hdSeaStage && addr < hdSeaStage+64000 {
		p.recordActiveWrite(addr, value)
		p.stage[addr-hdSeaStage] = hdSmallCell{}
		return
	}
	if p.active && p.scaledActive && (addr < hdBuildingCanvas || addr >= hdBuildingCanvas+64000) {
		cs, ip := p.h.m.CPU.OpAddr()
		if cs == 0xd66 && (ip == 0x22e || ip == 0x272 || ip == 0x29e) {
			p.outside = true
		}
	}

	if addr >= hdBuildingCanvas && addr < hdBuildingCanvas+64000 {
		p.write(addr, old, value)
		return
	}
	if (addr >= hdSeaStage && addr < hdSeaStage+64000) || addr >= 0xa0000 || p.accepted == 0 {
		return
	}
	cell, src, ok := p.copySource(addr, value)
	delete(p.backing, addr)
	if !ok || src < int(hdBuildingCanvas) || src >= int(hdBuildingCanvas)+64000 {
		return
	}
	p.backing[addr] = cell
	p.bufferSaves++
	p.frames[cell.slot].bufferSaves++
	if uint64(len(p.backing)) > p.peakBuffered {
		p.peakBuffered = uint64(len(p.backing))
	}
}
func (p *hdSmallRuntime) copySource(addr uint32, value byte) (hdSmallCell, int, bool) {
	m := p.h.m
	c := m.CPU
	cs, ip := c.OpAddr()
	if cs != 0xcba || ip != 0xca {
		return hdSmallCell{}, 0, false
	}
	pc := int(cs)*16 + int(ip)
	if pc < 0 || pc+16 > len(m.Mem) || !bytes.Equal(m.Mem[pc:pc+16], []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}) {
		return hdSmallCell{}, 0, false
	}
	delta := int(addr) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
	src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
	if delta < 0 || delta >= 2 || int(c.R[golem.SI])+delta >= 65536 || int(c.R[golem.DI])+delta >= 65536 || src < 0 || src >= 0xa0000 || src >= len(m.Mem) || m.Mem[src] != value {
		return hdSmallCell{}, 0, false
	}
	if src >= int(hdSeaStage) && src < int(hdSeaStage)+64000 {
		cell := p.stage[src-int(hdSeaStage)]
		ok := cell.owned && int(cell.slot) < len(p.frames) && cell.native == value && p.frames[cell.slot].scaled100 && c.Flags&0x400 == 0
		return cell, src, ok
	}
	var cell hdSmallCell
	if src >= int(hdBuildingCanvas) && src < int(hdBuildingCanvas)+64000 {
		cell = p.visible[src-int(hdBuildingCanvas)]
	} else {
		cell = p.backing[uint32(src)]
	}
	return cell, src, cell.owned && int(cell.slot) < len(p.frames) && cell.native == value && (!p.frames[cell.slot].scaled100 || c.Flags&0x400 == 0)
}

func (p *hdSmallRuntime) recordActiveWrite(addr uint32, value byte) {
	if !p.active {
		return
	}
	f := &p.frames[p.selected]
	m := p.h.m
	cs, ip := m.CPU.OpAddr()
	base := uint32(hdBuildingCanvas)
	if p.destination != 0 {
		base = p.destination
	}
	pos := int(addr) - int(base)
	x, y := pos%320-p.x, pos/320-p.y
	bit := uint8(0)
	codes := hdSmallWriterCodes
	expectedCS := uint16(0xd46)
	if p.scaledActive {
		expectedCS = 0xd66
		codes = hdSmallScaledWriterCodes
		switch ip {
		case 0x22e:
			bit = 1
		case 0x272:
			bit = 2
		case 0x29e:
			bit = 4
		}
	} else {
		switch ip {
		case 0x181:
			bit = 1
		case 0x1b4:
			bit = 2
		case 0x1d2:
			bit = 4
		}
	}
	pc := int(cs)*16 + int(ip)
	valid := cs == expectedCS && bit&f.writers != 0 && bytes.Equal(m.Mem[pc:pc+16], codes[ip]) && x >= 0 && x < f.w && y >= 0 && y < f.h
	if p.scaledActive {
		valid = valid && addr >= base && addr < base+64000 && addr == uint32(m.CPU.Seg[golem.ES])*16+uint32(m.CPU.R[golem.BX]) && m.CPU.Seg[golem.DS] == p.sourceDS && int(m.CPU.R[golem.SI]) >= p.sourceOffset && int(m.CPU.R[golem.SI]) <= p.sourceOffset+f.encodedLen
	}
	if valid {
		k := y*f.w + x
		p.counts[k]++
		p.writes[k] = value
	} else {
		p.outside = true
	}
}

var hdSmallScaledWriterCodes = map[uint16][]byte{
	0x22e: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0x47, 0xfe, 0xcc, 0x74, 0x02, 0xeb, 0xd7, 0xeb, 0xba},
	0x272: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0x47, 0xfe, 0xcc, 0x74, 0x02, 0xeb, 0xd8, 0xeb, 0xbc},
	0x29e: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0x47, 0xeb, 0x96, 0x5a, 0x5b, 0x5f, 0x03, 0x5e, 0xfe},
}

func hdSmallScaledPaletteSupported(pal []byte) bool {
	if len(pal) != 768 {
		return false
	}
	var projection []byte
	for _, v := range []byte{47, 57, 58, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 100, 108, 109, 110, 111, 113, 116, 132, 133, 137, 138} {
		projection = append(projection, v)
		projection = append(projection, pal[int(v)*3:int(v)*3+3]...)
	}
	return hash(projection) == "1be3ed349ef54783069d4ee2bf3ba3636e5ec92afadc1699258017fffd568cc6"
}

func (f hdSmallFrame) paletteSupported(palette []byte) bool {
	if f.paletteSHA == "" {
		return true
	}
	if len(palette) != 768 || len(f.paletteIndices) == 0 {
		return false
	}
	projection := make([]byte, 0, len(f.paletteIndices)*4)
	for _, i := range f.paletteIndices {
		projection = append(projection, i)
		projection = append(projection, palette[int(i)*3:int(i)*3+3]...)
	}
	return hash(projection) == f.paletteSHA
}
