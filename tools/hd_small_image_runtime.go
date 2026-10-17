// 規格065 R57及規格070 R72／R73／R74 READY：61來源共用追蹤，除100沿人物層外皆有正式生成素材。
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
	writes                                    [256]byte
	counts                                    [256]uint16
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
	m := p.h.m
	c := m.CPU
	if p.active {
		if c.Seg[golem.CS] == p.retCS && c.IP == p.retIP && c.R[golem.SP] == p.sp+10 {
			p.finish()
		} else if m.Steps-p.start > 100000 || (c.Seg[golem.CS] == 0xd46 && c.IP == 0xa) {
			p.active = false
			p.rejected++
			p.frames[p.selected].rejected++
		}
	}
	if c.Seg[golem.CS] != 0xd46 || c.IP != 0xa || p.active {
		return
	}
	pc := int(c.Seg[golem.CS])*16 + int(c.IP)
	if !bytes.Equal(m.Mem[pc:pc+12], []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		return
	}
	slot := -1
	for i, f := range p.frames {
		if c.R[golem.AX] == uint16(f.ordinal+1) {
			slot = i
			break
		}
	}
	if slot < 0 {
		return
	}
	f := &p.frames[slot]
	stack := int(c.Seg[golem.SS])*16 + int(c.R[golem.SP])
	if stack+10 > len(m.Mem) {
		return
	}
	words := [5]uint16{}
	for i := range words {
		words[i] = binary.LittleEndian.Uint16(m.Mem[stack+i*2:])
	}
	off := uint16((c.R[golem.AX]&0x7fff)*12 + words[3] + 0x36)
	at := int(words[4])*16 + int(off)
	if at+12 > len(m.Mem) {
		return
	}
	record := [6]uint16{}
	for i := range record {
		record[i] = binary.LittleEndian.Uint16(m.Mem[at+i*2:])
	}
	source := int(record[1])*16 + int(record[0])
	if source+f.encodedLen > len(m.Mem) || hash(m.Mem[source:source+f.encodedLen]) != f.encodedSHA {
		return
	}
	descriptor := int(c.Seg[golem.DS])*16 + int(c.R[golem.BX])
	if descriptor+8 > len(m.Mem) {
		return
	}
	d := [4]uint16{}
	for i := range d {
		d[i] = binary.LittleEndian.Uint16(m.Mem[descriptor+i*2:])
	}
	x, y := int(int16(c.R[golem.DX])), int(int16(words[2]))
	if d != [4]uint16{200, 320, 0, 0x2cae} || int(record[4]) != f.w || int(record[5]) != f.h || x < 0 || x+f.w > 320 || y < 0 || y+f.h > 200 {
		p.rejected++
		f.rejected++
		return
	}
	p.selected, p.active, p.outside, p.x, p.y = slot, true, false, x, y
	p.start, p.sp, p.retCS, p.retIP = m.Steps, c.R[golem.SP], words[1], words[0]
	p.writes, p.counts = [256]byte{}, [256]uint16{}
	if p.trace {
		p.entry = map[string]any{"ordinal": f.ordinal, "entry_step": m.Steps, "registers": c.R, "segments": c.Seg, "stack": words, "record_far": fmt.Sprintf("%04X:%04X", words[4], off), "record": record, "source_far": fmt.Sprintf("%04X:%04X", record[1], record[0]), "source_sha256": hash(m.Mem[source : source+f.encodedLen]), "rect": [4]int{x, y, x + f.w, y + f.h}}
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
			p.visible[i] = hdSmallCell{true, uint32(k), p.writes[k], uint16(p.selected)}
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
	if p.active {
		f := &p.frames[p.selected]
		x, y := i%320-p.x, i/320-p.y
		bit := uint8(0)
		switch ip {
		case 0x181:
			bit = 1
		case 0x1b4:
			bit = 2
		case 0x1d2:
			bit = 4
		}
		pc := int(cs)*16 + int(ip)
		if cs == 0xd46 && bit&f.writers != 0 && bytes.Equal(m.Mem[pc:pc+16], hdSmallWriterCodes[ip]) && x >= 0 && x < f.w && y >= 0 && y < f.h {
			k := y*f.w + x
			p.counts[k]++
			p.writes[k] = value
		} else {
			p.outside = true
		}
	}
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
		if a.art == nil {
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
		return hdSmallCell{}, src, false
	}
	var cell hdSmallCell
	if src >= int(hdBuildingCanvas) && src < int(hdBuildingCanvas)+64000 {
		cell = p.visible[src-int(hdBuildingCanvas)]
	} else {
		cell = p.backing[uint32(src)]
	}
	return cell, src, cell.owned && int(cell.slot) < len(p.frames) && cell.native == value
}
