// 規格061 R103 READY：追加既有第47幀原圖與來源。
// 規格061 R91／064 READY：已驗建築來源正式HD顯示，範圍依各規格。
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

type hdNineFrame struct {
	ordinal, w, h, encodedLen, opaque    int
	encodedSHA, writesSHA, artSHA, file  string
	artW, artH                           int
	sample, content                      [4]int
	writers                              uint8
	art                                  *image.RGBA
	accepted, rejected, paints, restores uint64
}

var hdNineFrames = []hdNineFrame{
	{ordinal: 16, w: 73, h: 18, encodedLen: 713, opaque: 504, encodedSHA: "37e3c67aad3611c0d6098cd3804fa17a6a33d8b0bf66e6df3e038089388a4568", writesSHA: "6c6c6b9ad00ffec4ae37390daa63f5d4e95ddfc473ee8fdf1443d131073df141", artSHA: "4378783b1ea54f32af12047fb06f260b496d68459f1eaacb5d42d5231c11ecd1", file: "building-016.png", artW: 2170, artH: 725, sample: [4]int{8, 119, 2162, 609}, content: [4]int{0, 0, 73, 18}, writers: 6},
	{ordinal: 21, w: 23, h: 27, encodedLen: 531, opaque: 446, encodedSHA: "d50481bdb7cfbb742035730387bb72601750c1cce584a47b9099034b410e38c8", writesSHA: "39680bcc21bfac1a7c8aa353948022ae6cdf1755882824a05b1177373a6de4b5", artSHA: "f81583f35c5102290424fd6575b67f08e47ab2488af61ed67eea0244fafe46f7", file: "building-021.png", artW: 1158, artH: 1358, sample: [4]int{20, 29, 1143, 1263}, content: [4]int{0, 2, 23, 27}, writers: 6},
	{ordinal: 27, w: 23, h: 27, encodedLen: 570, opaque: 465, encodedSHA: "51dd0b1f21b29b0e7ee6f7e07d93e5418ed3368a11eaedffc81aa69b954e7d31", writesSHA: "379715daae1fc96a7496bc9732a66ab73df9137c5fc5fed1aea668654b8c76b7", artSHA: "59d78ffbe53983600336fa7b0919032fcb95f79f744f31c03242e6c2f7f4f4b1", file: "building-027.png", artW: 1158, artH: 1359, sample: [4]int{40, 16, 1120, 1336}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 35, w: 44, h: 22, encodedLen: 752, opaque: 507, encodedSHA: "8d75b678630f769528a01f79c897dcc33f982353c93674997fc02fc9df32c198", writesSHA: "146e920bfced13314162b208f61d37c19b166c83321703ad2c86b577b11e773b", artSHA: "05832b749f1cca7e97af3a8cdd3417c12284df2d6db43e4e6656de65c7a44e58", file: "building-035.png", artW: 1774, artH: 887, sample: [4]int{83, 111, 1733, 804}, content: [4]int{0, 0, 44, 21}, writers: 7},
	{ordinal: 39, w: 23, h: 27, encodedLen: 541, opaque: 459, encodedSHA: "29dafe80be32105e570abf822fea90b1ce73bcc206523aa758346b24066c8936", writesSHA: "c2534296a3f6ff776771ee5c1069ff95b8141511f2790629359a34f3978212bb", artSHA: "2c2f7f9c3c325c64b919b02ca37fd8876ad74850fa7f7e737ef96d15f6a1b8c0", file: "building-039.png", artW: 1158, artH: 1359, sample: [4]int{37, 17, 1138, 1300}, content: [4]int{0, 0, 23, 25}, writers: 6},
	{ordinal: 42, w: 53, h: 37, encodedLen: 1176, opaque: 848, encodedSHA: "349af0f0328751db570320e0964f65a50fc6c7b393b991cd61e886a429536582", writesSHA: "d11c6733d9f05e82872a4eb5a8e7e792bd3b5a0ccbfd0dc50ff97f4c6e36bfd9", artSHA: "34f7ee08d3429ed6a6659b5c5eb6aa1ecfdf1656a814a494658368c475fdd8d4", file: "building-042.png", artW: 1502, artH: 1047, sample: [4]int{24, 10, 1502, 1034}, content: [4]int{1, 0, 53, 36}, writers: 7},
	{ordinal: 43, w: 44, h: 22, encodedLen: 546, opaque: 369, encodedSHA: "31756e82c00bdbbd5dee53414b08061e47bf102e87cc3d70beef9be0dd5116aa", writesSHA: "4e40c62f6fae8204e485ddd6207239cd3c9031ea0ff234660d4fd35c56dd362c", artSHA: "0d9ad7021e2ddf5a2062e6705ba0be869e4ac3781046262eec0b4984a371b928", file: "building-043.png", artW: 1774, artH: 887, sample: [4]int{12, 44, 1766, 852}, content: [4]int{0, 1, 44, 22}, writers: 7},
	{ordinal: 44, w: 23, h: 27, encodedLen: 462, opaque: 262, encodedSHA: "f9bb3cc9064ce58f05443b8671a870d69fde96667e9a3dde1c24763b1c368332", writesSHA: "687fc5f1be762b2d8dea63c8f58ec52efa3234a6e5acc122bf225b4898116a8c", artSHA: "004fdb0045fc47653fd40beef438d0f2922933639a68c95a1d7b504ed908afed", file: "building-044.png", artW: 1158, artH: 1359, sample: [4]int{17, 21, 1138, 1323}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 45, w: 75, h: 48, encodedLen: 1591, opaque: 1069, encodedSHA: "129934aa9808419a2164569da49363b9a8c8486a0460fd9da876cb641b797de1", writesSHA: "4cd7ef3f6f68a770158bddf9b98b1797c5c204acfbe83596bfc6bfaa33517627", artSHA: "07049354109ff9bee01f103a2b408d227a607b8bba138cefc9de5af840f99915", file: "building-045.png", artW: 1568, artH: 1003, sample: [4]int{18, 0, 1568, 979}, content: [4]int{1, 0, 75, 48}, writers: 6},
	{ordinal: 9, w: 53, h: 37, encodedLen: 1254, opaque: 1095, encodedSHA: "8900416036b739238f3d36ef0bd6de7c64cc92e2273658c866e233a328380d8c", writesSHA: "80e2c7b872906ce4fc27a12926b6a9be2a77c90f75c509f0524346254781f0d6", artSHA: "bc7057fa60db21a120f3d2fd81d59f7ae77cfa56ac351aa6df9d455f7bac29b6", file: "building-009.png", artW: 1500, artH: 1049, sample: [4]int{9, 57, 1490, 1004}, content: [4]int{0, 0, 53, 36}, writers: 6},
	{ordinal: 0, w: 73, h: 18, encodedLen: 903, opaque: 808, encodedSHA: "1876dfdb3f3142fe7a52b8e5cb5fbb41611b6e7863fde78af44cd5c786aaf49e", writesSHA: "42173fc2d6aa00420b9111b9714a28049fd8d644a56c620933ff5cd0174bb89c", artSHA: "be73e486cc1a2251df5b77b001268404e3aa9149f1a0d613215953b974951f07", file: "building-000.png", artW: 2120, artH: 742, sample: [4]int{15, 133, 2105, 570}, content: [4]int{0, 3, 73, 18}, writers: 4},
	{ordinal: 1, w: 73, h: 18, encodedLen: 1131, opaque: 1024, encodedSHA: "24f1681a125518d254ed38554e0635b0220fadfff8610dbe0100cfe3f8b9a93b", writesSHA: "53d54df70ed0d97ae75d1a530c7d1e6a0a49d1107078eae7476fdaaa2f971a0f", artSHA: "fbb98fe74f66c1e71223868888d7e2f03d025af7813899a68490160c8901f8de", file: "building-001.png", artW: 2120, artH: 742, sample: [4]int{21, 83, 2100, 643}, content: [4]int{0, 0, 73, 18}, writers: 6},
	{ordinal: 2, w: 73, h: 18, encodedLen: 1088, opaque: 1038, encodedSHA: "6064567b9d48b5c3b72768dc0a7d76a2a1184c891f083e15604454c2dbb49b4c", writesSHA: "f184c76aba2746d676e1287f476ce50ca1a53c5bc241400f980b00060ce8ef3f", artSHA: "28d992b808439e4ec0a9117f14ca645eec903e6ebde631b324894f8caf5d952f", file: "building-002.png", artW: 2117, artH: 743, sample: [4]int{38, 128, 2079, 610}, content: [4]int{0, 0, 73, 18}, writers: 6},
	{ordinal: 3, w: 44, h: 22, encodedLen: 775, opaque: 663, encodedSHA: "cd1eeef2db89db69dd21bd9c9442e8f7799b36c43a108f4bc0e3fe582929fcc0", writesSHA: "33f06760b51f9ac523fa787c99484f8224e20c07d581f8b429d44d61d824b75a", artSHA: "7d7ba364a4c80631d8d17a21c999d64b17fbe9c94958498b9f1926e43b04858b", file: "building-003.png", artW: 1774, artH: 887, sample: [4]int{65, 112, 1725, 814}, content: [4]int{0, 0, 44, 22}, writers: 7},
	{ordinal: 4, w: 44, h: 22, encodedLen: 774, opaque: 711, encodedSHA: "21a85ba23b0270de975cf08b1a7edca71ac5638c883ae88538e1c7629e500761", writesSHA: "2d6d0ed9aa214dde39c67401eb986bf2f6ba1605b260889d4b1f3c10ce0d9dc9", artSHA: "c7150437bc61edddc4491c85cfd28a283d832eb8eb1e3735495c0fbb0c9bd01b", file: "building-004.png", artW: 1774, artH: 887, sample: [4]int{52, 79, 1750, 805}, content: [4]int{0, 1, 44, 22}, writers: 6},
	{ordinal: 5, w: 44, h: 22, encodedLen: 923, opaque: 882, encodedSHA: "0417dc81babdb1d631469e230388255505840f541e14003e70a9d8d5fecab263", writesSHA: "54b2b0117c1873fa32cee74f03dcb0f4faaac3a814c8df021336597a406457cb", artSHA: "600455bdefddde32395477711a0b0b6bd619dad98dd940d65b729bb526f51b88", file: "building-005.png", artW: 1774, artH: 887, sample: [4]int{92, 84, 1733, 797}, content: [4]int{0, 0, 44, 22}, writers: 6},
	{ordinal: 6, w: 75, h: 48, encodedLen: 1630, opaque: 1127, encodedSHA: "7e8ffc27b1740a6e4ef5c472dedaa63c787b7dc4e356284b3b909f63784ce752", writesSHA: "f2c9ea8ce830fad72a2a1cf9fa8d6e39d2ac14636547a6b27b8509ef72ae30a7", artSHA: "5ece7efa3f4f0d5b644a19fd7dd2e8cf85a16fc16328fd6472886674d9b9e587", file: "building-006.png", artW: 1569, artH: 1003, sample: [4]int{20, 24, 1569, 983}, content: [4]int{1, 0, 75, 48}, writers: 6},
	{ordinal: 7, w: 75, h: 48, encodedLen: 1653, opaque: 1130, encodedSHA: "5830c1bae22b62b881f9ca599b87e6773a003b2323a84e6d4cba91337e085a1b", writesSHA: "0593e721473bf5a71934e3120da408fb32f3349ad694c4ee1864cab132be846e", artSHA: "37722b6edb876c96b6fc2f186fc98ac211292973e3fcd909f0f67a4a7165feef", file: "building-007.png", artW: 1568, artH: 1003, sample: [4]int{24, 3, 1568, 1000}, content: [4]int{1, 0, 75, 48}, writers: 6},
	{ordinal: 8, w: 75, h: 48, encodedLen: 1740, opaque: 1175, encodedSHA: "1baef8e1ec22e365e37c1eed7881ee778abaab80a1b57442dc376c060bb5251d", writesSHA: "e5ecb0b82689ef7df2c5d4bbc77ad773cda868e4b3f0907a09027fa5ecffc545", artSHA: "2dcbd2f491626e43ef19f19b4f504138aa28f7b3c61865eea55feb9e243ca2be", file: "building-008.png", artW: 1568, artH: 1003, sample: [4]int{3, 0, 1568, 1003}, content: [4]int{1, 0, 75, 48}, writers: 6},
	{ordinal: 12, w: 44, h: 22, encodedLen: 792, opaque: 639, encodedSHA: "4beacffbb2182895e9a64136061856b8c63189dd825d279425ad28081a8eb62f", writesSHA: "e59a17eba39565660862374269673246b02ba13ebffe5b9199751e2331ea98a6", artSHA: "0a209fc01aba2700476081cef9c21a45350a57cb459269845aeb98ec220ba63e", file: "building-012.png", artW: 1774, artH: 887, sample: [4]int{10, 13, 1764, 830}, content: [4]int{0, 1, 43, 22}, writers: 6},
	{ordinal: 13, w: 44, h: 22, encodedLen: 751, opaque: 699, encodedSHA: "2e50c1e9da59c2951d9289c68d9c82a50530120d60486cf2b881dfba5d4ee486", writesSHA: "768966fba267b8a578b6681721e5782dcc5e34df0cd0a2faf0a3eb27f9c8e212", artSHA: "111a5a75f2ba31f6cc788a53f3b70d847349f6abd17a661d7aa2bee88282e57a", file: "building-013.png", artW: 1774, artH: 887, sample: [4]int{9, 140, 1771, 737}, content: [4]int{0, 4, 44, 21}, writers: 6},
	{ordinal: 14, w: 44, h: 22, encodedLen: 910, opaque: 828, encodedSHA: "2c9ae2ab4721dd8b369c0d6e8e6a530943ae428335f8d6da7e10550272c079cd", writesSHA: "042e493634ac1019dbe1acf5e376bd56642609b6ed66c5891365ff9f7a42968b", artSHA: "e61345a39b9f68d3623cb50ce089f99d1619ff0aec038172c0b8859ea9974d85", file: "building-014.png", artW: 1774, artH: 887, sample: [4]int{25, 29, 1749, 841}, content: [4]int{0, 0, 44, 22}, writers: 6},
	{ordinal: 15, w: 44, h: 22, encodedLen: 796, opaque: 684, encodedSHA: "f97813c95fc494a09a79fb93a15e5045237671e3b961f2783e4c48e02047d399", writesSHA: "5600a93bd21c326989615be5a39f2cb4c6edd15ffc4801b2b9408111c53e25a3", artSHA: "de7baee7faf1ec9ef725b74dbb22e244cefc101209bb5c3912107965044f4202", file: "building-015.png", artW: 1774, artH: 887, sample: [4]int{66, 55, 1709, 818}, content: [4]int{0, 1, 43, 22}, writers: 6},
	{ordinal: 18, w: 23, h: 27, encodedLen: 497, opaque: 410, encodedSHA: "2c02b5c6f29937b22e4a05b1ab3b729c54ef7a95ff45451168118106907ebc7e", writesSHA: "ecc35abb2f51122138d9aca0d8a4b9c82c1582c4356f014259ffb855cf36983d", artSHA: "b00bd9cde6e143b3307f670f70899cefa20c02dc87e3073b9adc9d755f130968", file: "building-018.png", artW: 1158, artH: 1359, sample: [4]int{92, 91, 1149, 1305}, content: [4]int{0, 2, 23, 27}, writers: 6},
	{ordinal: 19, w: 23, h: 27, encodedLen: 564, opaque: 490, encodedSHA: "5395ba55c8e365637c2ba339a780fb0697c45994b7b9bda1df260230d8c7c4f6", writesSHA: "9a5b2e09aa68ee631e6045b4201600928a71c01bc991783365e9e69275caaba8", artSHA: "fdabcccc60857158ef61b5fcfa63d7371dc4f60d3d0e01fd1766064f2dc37fd5", file: "building-019.png", artW: 1158, artH: 1359, sample: [4]int{107, 106, 1111, 1266}, content: [4]int{0, 1, 23, 27}, writers: 6},
	{ordinal: 20, w: 23, h: 27, encodedLen: 647, opaque: 591, encodedSHA: "2a2c95aa34237fc3581f49de344c76da9b355e800acce20d3841e915e343ab25", writesSHA: "8b04f951f60559a7e6f74e82a7e400dc10ac61acba2d214b327af0b8b65429cf", artSHA: "f14a40b5750c9c0ed1cc6f72594cf7e50415a43b9449a8083d85ad04c222fa4a", file: "building-020.png", artW: 1158, artH: 1359, sample: [4]int{113, 79, 1073, 1278}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 22, w: 23, h: 27, encodedLen: 597, opaque: 524, encodedSHA: "0a5004b578d0520cc3d3a6672424ec672797235946048328aaeb53b5ff7246fc", writesSHA: "954166f2fc8727c1489d75627c595b55f91e69fd8c94caa828615bdc77e10397", artSHA: "e3c9e76f560b741e6bfcdc545959c0b883d945614c21c0396f3dfd0508aa0b3b", file: "building-022.png", artW: 1158, artH: 1359, sample: [4]int{46, 79, 1126, 1304}, content: [4]int{0, 1, 23, 27}, writers: 6},
	{ordinal: 23, w: 23, h: 27, encodedLen: 601, opaque: 559, encodedSHA: "ab8790c65a319ad80dcc388b91ea0ad20e427f5f4cbb8bba51d3f8b3a21b6d90", writesSHA: "3be677ab9cbe60774f609eb46bd5da068cacb1e6998112827524b42554c4c5e5", artSHA: "c50fc75b33e60e5a6092688f0c03cff5d5eea024b85fde18cb4039726eceaafb", file: "building-023.png", artW: 1158, artH: 1359, sample: [4]int{48, 29, 1126, 1301}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 25, w: 23, h: 27, encodedLen: 533, opaque: 431, encodedSHA: "1f9bbd236f1b3087241c59b75ce3af4a1508869e7f60c23f6354f60bf548dd32", writesSHA: "2e1c72a0512b92b8c83c4313ee55994945e384a8a3798e94a4ac3b4d398d7743", artSHA: "1ec3dc44f3a942e3bec47b824c9fbc96ad37f162f2c34078b46f25bccb46e086", file: "building-025.png", artW: 1158, artH: 1359, sample: [4]int{89, 97, 1088, 1268}, content: [4]int{0, 1, 23, 27}, writers: 7},
	{ordinal: 26, w: 23, h: 27, encodedLen: 617, opaque: 540, encodedSHA: "31910722e99512d07bcf2faca4f6f05bb3403b56cdb3495ea03d2f68e5e4edf6", writesSHA: "421f728124e050d030cd322b6cc05d2c83e391065fde1bd06ff1516313f01533", artSHA: "7346b1ce2df7b0a586e25b2b51501dc5472abb0801b54b22ceeb679cebc8879e", file: "building-026.png", artW: 1158, artH: 1359, sample: [4]int{114, 66, 1045, 1294}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 28, w: 23, h: 27, encodedLen: 593, opaque: 496, encodedSHA: "362f7937e2392e442894a92d5e065addd1420732efd8e694991f657fe4540c11", writesSHA: "0e8a4b312343b81951d18ad84fc6da8afc5cb88439f834b08ecd422a82ff6e97", artSHA: "40f608ea2942f2b1d28d8656b8dffce085d78cd63e652493570f23c6e4bfbefa", file: "building-028.png", artW: 1158, artH: 1359, sample: [4]int{38, 47, 1146, 1280}, content: [4]int{0, 1, 23, 27}, writers: 4},
	{ordinal: 29, w: 23, h: 27, encodedLen: 639, opaque: 557, encodedSHA: "1ab49220e290596299904fa1da364621116eceb2469316c5ddbc59476670d387", writesSHA: "42667c48236478ccf4532c5202c4044dcca0bada44a24db011c60b0e9d61daeb", artSHA: "f8d614256699f655cb03234442a6c9f54f50e748a823a1a5d79dffc6efa70700", file: "building-029.png", artW: 1158, artH: 1359, sample: [4]int{73, 48, 1102, 1310}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 33, w: 23, h: 27, encodedLen: 535, opaque: 474, encodedSHA: "1d701d4774914a2cd63e98a1c63d433b6b2566d7d94ccca07afcd493e227dcc1", writesSHA: "6f58aab578e507673ef98555a4e107bfd23c08e409d6bf579f438bad1253809f", artSHA: "727e709cfea47ed0b39e17177b2d1a466179a35deb92899f0cac9a631bbcb704", file: "building-033.png", artW: 1158, artH: 1359, sample: [4]int{134, 158, 1046, 1221}, content: [4]int{0, 1, 22, 27}, writers: 6},
	{ordinal: 34, w: 23, h: 27, encodedLen: 622, opaque: 592, encodedSHA: "9bdea7d225a7feee5ee675b6e3bdc98de654dc6ac7939e2492114e4d01db519f", writesSHA: "8f988330fdeb43e273f8c221cd4ee73bc0d0aa6c0c6a6a67e5cbee3f6a98a011", artSHA: "cf141a3eee4401f15f3298ecc107aded316d4e16b5836b38f02338788d2b520c", file: "building-034.png", artW: 1158, artH: 1359, sample: [4]int{92, 58, 1092, 1305}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 36, w: 44, h: 22, encodedLen: 778, opaque: 670, encodedSHA: "773f00066710246b280054fbef4fed6066f1af21bdba86c95a57b31a5832679b", writesSHA: "4cc602c5cbb6df3b307b161f92007e580349773a3349b01a0a64d0df21c7cc59", artSHA: "f11c3b4b58a8768f39a28bc9c5d086e20018e0374846adf6fa9594fab6c7246c", file: "building-036.png", artW: 1774, artH: 887, sample: [4]int{58, 59, 1751, 854}, content: [4]int{0, 0, 44, 22}, writers: 6},
	{ordinal: 37, w: 53, h: 37, encodedLen: 1284, opaque: 1048, encodedSHA: "52b17b56cd042dda27728c93dd7c5bae787408f7b62a0e28196c8bd84f5a62b7", writesSHA: "2ad6a7ecac24374952cdf3152b5d9bfbc298705cb6d0701a86bfc182fa660859", artSHA: "f73e86dad84756ebc730c411a1c5a5463ae2c53a2361757b0305542a2973ed94", file: "building-037.png", artW: 1501, artH: 1048, sample: [4]int{7, 10, 1495, 1035}, content: [4]int{0, 0, 53, 37}, writers: 6},
	{ordinal: 38, w: 53, h: 37, encodedLen: 1580, opaque: 1413, encodedSHA: "42bbcb17cffb6637dad5b9c66a83f573893e0bb85de143cad23d11d55d03e9b5", writesSHA: "d6485e4974fe678f2c897dfec41a9175f4610dee3911255d2895edd7a11ffcf0", artSHA: "0efcf5e97bc578a901c0d5a79bdec7ffd57d9b5fe77e36ed946252d6a0e50979", file: "building-038.png", artW: 1501, artH: 1048, sample: [4]int{10, 8, 1494, 1034}, content: [4]int{0, 0, 53, 37}, writers: 6},
	{ordinal: 40, w: 23, h: 27, encodedLen: 600, opaque: 514, encodedSHA: "6588008b35df0af9d24cdf2ff026fad206747c7a2406ca4595c04df3e33a56bd", writesSHA: "783e3f846166d9974a564cb3e3d432ebe0040f1af6783ac76f9a110449b4a05d", artSHA: "462163db5c17fcc5cd561c1eafcfd18330bf0cc1129e298e356a618e27abd0c6", file: "building-040.png", artW: 1158, artH: 1359, sample: [4]int{19, 57, 1148, 1246}, content: [4]int{0, 0, 23, 27}, writers: 7},
	{ordinal: 41, w: 23, h: 27, encodedLen: 618, opaque: 546, encodedSHA: "c5bbef54aea58981b5c62936242c8bb515170bc0488cfba752ec066b6db35f01", writesSHA: "dc64ee40b4349d45cd6f0de42b4cafc2ccce6318f46f3f606f6612b724ff419b", artSHA: "ab4ec26b3db95262bac5e0bdba170bd56e4bf26f3684187789c6401dba7b9cc6", file: "building-041.png", artW: 1158, artH: 1359, sample: [4]int{59, 75, 1121, 1315}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 46, w: 44, h: 22, encodedLen: 591, opaque: 401, encodedSHA: "cc064e7c579538dd4618e34b1fc3158757de6dc263e32121266e1d14ce37e559", writesSHA: "addc9340c4000d482cf30f51a6aebe1f8128289e877e0f9589fb03bcf467e18a", artSHA: "21a027f4373c9432668675a2e2a0deb89c5d67977c8dbe1fd20fa4ed5407b68d", file: "building-046.png", artW: 1774, artH: 887, sample: [4]int{13, 136, 1761, 761}, content: [4]int{0, 0, 44, 22}, writers: 7},
	{ordinal: 47, w: 44, h: 22, encodedLen: 844, opaque: 710, encodedSHA: "4c49e03bbad2f6294365bf83f3b07e6826cde9e19d780c4c6bf106d9a8f88fb7", writesSHA: "fe5931bf2dce4489660dd622d1899d61c14cda37d69912ef4b2542851bb10a7e", artSHA: "31225a16cea5cba6b723958871834e6e998d46242a070ac9b8703a0efa13c69e", file: "building-047.png", artW: 1774, artH: 887, sample: [4]int{0, 0, 1774, 887}, content: [4]int{0, 0, 44, 22}, writers: 7},
}
var hdNineWriterCodes = map[uint16][]byte{
	0x181: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x02, 0xeb, 0xe7, 0xeb, 0xd0, 0x3b},
	0x1b4: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x03, 0xeb, 0xe7, 0x90, 0xeb, 0xcc},
	0x1d2: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xeb, 0xb5, 0x90, 0x5a, 0x5b, 0x03, 0x5e, 0xfe, 0x79},
}

type hdNineCell struct {
	owned  bool
	local  uint16
	native byte
	slot   uint8
}
type hdNinePending struct {
	cell       hdNineCell
	old, value byte
	cursor     int
}
type hdNineRuntime struct {
	h                                   *hdRuntime
	frames                              []hdNineFrame
	visible                             [64000]hdNineCell
	pending                             map[int]hdNinePending
	active, outside                     bool
	selected                            int
	x, y                                int
	sp, retCS, retIP                    uint16
	start, revision, accepted, rejected uint64
	writes                              [3600]byte
	counts                              [3600]uint16
	trace                               bool
	calls, pairs                        []map[string]any
	entry                               map[string]any
}

func hdNineRead(path, want string, limit int64) ([]byte, error) {
	raw, err := hdReadFile(path, limit)
	if err != nil {
		return nil, err
	}
	if hash(raw) != want {
		return nil, fmt.Errorf("城內來源指紋不同：%s", path)
	}
	return raw, nil
}
func loadHDNineRuntime(h *hdRuntime, game, directory string) (*hdNineRuntime, error) {
	if h == nil || directory == "" {
		return nil, fmt.Errorf("城內來源需要既有HD及素材目錄")
	}
	if _, err := hdNineRead(filepath.Join(game, "BUILDING.SS"), hdBuildingFileSHA, 8<<20); err != nil {
		return nil, err
	}
	p := &hdNineRuntime{h: h, frames: append([]hdNineFrame(nil), hdNineFrames...), pending: map[int]hdNinePending{}}
	for i := range p.frames {
		f := &p.frames[i]
		raw, err := hdNineRead(filepath.Join(directory, f.file), f.artSHA, 8<<20)
		if err != nil {
			return nil, err
		}
		c, err := png.DecodeConfig(bytes.NewReader(raw))
		if err != nil || c.Width != f.artW || c.Height != f.artH {
			return nil, fmt.Errorf("城內來源原圖尺寸不同：%d", f.ordinal)
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		a, b := f.sample, f.content
		if a[0] < 0 || a[1] < 0 || a[2] <= a[0] || a[3] <= a[1] || a[2] > f.artW || a[3] > f.artH || b[0] < 0 || b[1] < 0 || b[2] <= b[0] || b[3] <= b[1] || b[2] > f.w || b[3] > f.h {
			return nil, fmt.Errorf("城內來源取樣邊界不同：%d", f.ordinal)
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
	h.m.WatchWrite(hdBuildingCanvas, hdBuildingCanvas+63999, func(_ *golem.Machine, a uint32, o, v byte) { p.write(a, o, v) })
	return p, nil
}
func (p *hdNineRuntime) beforeInstruction() {
	if p == nil {
		return
	}
	m := p.h.m
	c := m.CPU
	if p.active {
		if c.Seg[golem.CS] == p.retCS && c.IP == p.retIP && c.R[golem.SP] == p.sp+10 {
			p.finish()
		} else if m.Steps-p.start > 100000 {
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
	p.writes, p.counts = [3600]byte{}, [3600]uint16{}
	if p.trace {
		p.entry = map[string]any{"ordinal": f.ordinal, "entry_step": m.Steps, "registers": c.R, "segments": c.Seg, "stack": words, "record_far": fmt.Sprintf("%04X:%04X", words[4], off), "record": record, "source_far": fmt.Sprintf("%04X:%04X", record[1], record[0]), "source_sha256": hash(m.Mem[source : source+f.encodedLen]), "rect": [4]int{x, y, x + f.w, y + f.h}}
	}
}
func (p *hdNineRuntime) finish() {
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
			p.visible[i] = hdNineCell{true, uint16(k), p.writes[k], uint8(p.selected)}
		}
	}
	p.accepted++
	f.accepted++
	if p.trace {
		if len(p.calls) >= 20000 {
			panic("城內來源繪製紀錄超限")
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
func (p *hdNineRuntime) write(addr uint32, old, value byte) {
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
		if cs == 0xd46 && bit&f.writers != 0 && bytes.Equal(m.Mem[pc:pc+16], hdNineWriterCodes[ip]) && x >= 0 && x < f.w && y >= 0 && y < f.h {
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
					p.pending[i] = hdNinePending{p.visible[i], old, value, k}
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
								panic("城內來源游標紀錄超限")
							}
							p.pairs = append(p.pairs, map[string]any{"ordinal": f.ordinal, "step": m.Steps, "linear": addr, "source_cursor_index": k, "native": prior.cell.native, "local": prior.cell.local, "paint_old": prior.old, "paint_value": prior.value, "restore_old": old, "restore_value": value, "registers": m.CPU.R, "segments": m.CPU.Seg, "code16": fmt.Sprintf("%x", m.Mem[pc:pc+16])})
						}
					}
					return
				}
			}
		}
	}
	p.visible[i].owned = false
	clear(p.pending)
}
func (p *hdNineRuntime) receipt(f draftNativeFrame) map[string]any {
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
		sources[fmt.Sprint(a.ordinal)] = map[string]any{"ordinal": a.ordinal, "owned": counts[i][0], "valid": counts[i][1], "mask": masks[i], "accepted": a.accepted, "rejected": a.rejected, "cursor_paint_points": a.paints, "cursor_restore_points": a.restores, "painted": 0, "alpha_pixels": 0}
	}
	return map[string]any{"formal": true, "asset": "building-nine", "accepted": p.accepted, "rejected": p.rejected, "owned": owned, "valid": valid, "mask": mask, "sources": sources, "pending": len(p.pending), "revision": p.revision}
}
func (p *hdNineRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
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
